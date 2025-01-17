import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import schedule
import time

load_dotenv()

PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_HOST = os.getenv('PG_HOST')
PG_PORT = os.getenv('PG_PORT')
PG_DATABASE = os.getenv('PG_DATABASE')


engine = create_engine(f'postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@localhost:{PG_PORT}/{PG_DATABASE}')

df_table = pd.read_sql_table('events', engine)


def connect_to_database():
    try:
        conn = psycopg2.connect(
            host=os.getenv('PG_HOST'),
            port=os.getenv('PG_PORT'),
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
            database=os.getenv('PG_DATABASE'),
        )
        conn.set_client_encoding('UTF8')
        print("Conexão ao banco de dados bem-sucedida.")
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def fix_corrupted_text(s: str) -> str:
    """
    Tenta desfazer problemas de mojibake e sequências \\uXXXX.
    
    1) Converte escapes \\uXXXX em caracteres reais
       (por exemplo, '\\u00e1' -> 'á', '\\ud83d\\ude00' -> '😀').
    2) Conserta 'horÃ¡rio', 'clÃ­nica' etc. (caso sejam bytes UTF-8
       que foram interpretados como Latin-1).
    
    Se ainda sair estranho, tente inverter a ordem ou ajustar
    conforme cada caso de corrompimento.
    """
    try:
        # (A) Converte sequências \\uXXXX => caracteres reais
        s = s.encode('utf-8', errors='replace').decode('unicode_escape', errors='replace')

        # (B) Corrige "clÃ­nica" -> "clínica" (UTF-8 lido como Latin-1)
        s = s.encode('latin1', errors='replace').decode('utf-8', errors='replace')

        return s
    except Exception:
        return s  # fallback

############################################################
# 3. Buscar todos os events de type_name='user' ou 'bot'
############################################################
def fetch_all_events(conn):
    """
    Retorna sender_id, type_name, data (JSON string) da tabela events,
    filtrando somente 'user' ou 'bot'.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT sender_id, type_name, data
                FROM events
                WHERE type_name IN ('user','bot')
            """
            cur.execute(query)
            return cur.fetchall()
    except Exception as e:
        print(f"Erro ao buscar logs: {e}")
        return []

############################################################
# 4. Extrair e decodificar dados do JSON "data"
############################################################
def extract_data(row):
    """
    Decodifica o JSON em row['data'] (por ex: {"text":"...", "timestamp":..., "metadata":...}).
    Aplica fix_corrupted_text no campo text.
    Retorna dicionário com: {sender_id, type_name, assistant_id, text, timestamp}.
    """
    try:
        data_json = json.loads(row['data'])  # carrega a string JSON
        text_original = data_json.get('text', '')
        text_corrigido = fix_corrupted_text(text_original)
        timestamp_value = data_json.get('timestamp', 0)

        # extrai assistant_id se existir
        metadata = data_json.get('metadata', {})
        assistant_id = metadata.get('assistant_id')

        return {
            'sender_id': row['sender_id'],
            'type_name': row['type_name'],
            'assistant_id': assistant_id,
            'text': text_corrigido,
            'timestamp': float(timestamp_value) if timestamp_value else 0.0
        }
    except Exception as e:
        print(f"Erro ao extrair dados: {e}")
        return None

############################################################
# 5. Processar dados e salvar em "Conversations"
############################################################
def process_chatbot_data():
    print(f"[{datetime.now()}] Iniciando processamento de dados...")
    conn = connect_to_database()
    if not conn:
        return

    try:
        rows = fetch_all_events(conn)
        if not rows:
            print("Nenhum evento encontrado.")
            return

        # Agrupar as mensagens por sender_id
        sessions = {}

        for row in rows:
            item = extract_data(row)
            if not item:
                continue

            # Agrupa por sender_id
            sid = item['sender_id']
            if sid not in sessions:
                sessions[sid] = {
                    'assistant_id': item['assistant_id'],
                    'messages': []
                }

            sessions[sid]['messages'].append({
                'type_name': item['type_name'],
                'text': item['text'],
                'timestamp': item['timestamp']
            })

        # Ordenar e inserir/atualizar na tabela "Conversations"
        with conn.cursor() as cur:
            for sender_id, data in sessions.items():
                # Ordena a lista de mensagens pelo timestamp
                data['messages'].sort(key=lambda x: x['timestamp'])

                # Gera o JSON para armazenar em conversation_data
                conversation_data = {
                    'messages': data['messages']
                }

                # Transformar em string JSON sem re-escapar acentos
                conversation_data_str = json.dumps(conversation_data, ensure_ascii=False)

                # Faz o INSERT ... ON CONFLICT (sender_id) DO UPDATE ...
                cur.execute("""
                    INSERT INTO "Conversations" (sender_id, conversation_data, assistant_id, "createdAt", "updatedAt")
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (sender_id) DO UPDATE
                      SET conversation_data = EXCLUDED.conversation_data,
                          assistant_id = EXCLUDED.assistant_id,
                          "updatedAt" = EXCLUDED."updatedAt"
                """, [
                    sender_id,
                    conversation_data_str,
                    data['assistant_id'],
                    datetime.now(),
                    datetime.now()
                ])

        conn.commit()
        print("Concluído: textos descorrompidos e salvos em 'Conversations'!")
    except Exception as e:
        print(f"Erro durante o processamento: {e}")
        conn.rollback()
    finally:
        conn.close()

############################################################
# 6. Scheduler simples
############################################################
if __name__ == "__main__":
    # Executa a cada X segundos, se quiser
    schedule.every(10).seconds.do(process_chatbot_data)

    print("Script iniciado. Processamento a cada 10 segundos...")
    while True:
        schedule.run_pending()
        time.sleep(1)