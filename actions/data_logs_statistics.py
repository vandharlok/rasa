import os
import pandas as pd
import json
import datetime
import time
import schedule
import re 

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Carregar variáveis de ambiente
load_dotenv()

PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_HOST = os.getenv('PG_HOST')
PG_PORT = os.getenv('PG_PORT')
PG_DATABASE = os.getenv('PG_DATABASE')

# Criar engine do banco
engine = create_engine(
    f'postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}'
)

# -------------------------------------------------------------------
# Funções auxiliares de filtragem
def extract_utter_action(json_str):
    """
    Extrai 'utter_action' de um JSON aninhado, se existir.
    """
    try:
        json_data = json.loads(json_str)
        for key, value in json_data.items():
            if isinstance(value, dict):
                if 'utter_action' in value:
                    return value['utter_action']
                # Busca recursiva
                nested_result = extract_utter_action(json.dumps(value))
                if nested_result:
                    return nested_result
        return None
    except json.JSONDecodeError:
        return None

def filter_login_success(json_str):
    """
    Verifica se no JSON tem 'name': 'login_sucess' e 'value': True
    """
    try:
        json_data = json.loads(json_str)
        return (
            json_data.get("name") == "login_sucess"
            and json_data.get("value") is True
        )
    except json.JSONDecodeError:
        return False

def filter_event_completed(json_str):
    """
    Verifica se no JSON tem 'name': 'event_completed' e 'value': True
    """
    try:
        json_data = json.loads(json_str)
        return (
            json_data.get("name") == "event_completed"
            and json_data.get("value") is True
        )
    except json.JSONDecodeError:
        return False

def filter_event_modify_completed(json_str):
    """
    Verifica se no JSON tem 'name': 'event_modify_completed' e 'value': True
    """
    try:
        json_data = json.loads(json_str)
        return (
            json_data.get("name") == "event_modify_completed"
            and json_data.get("value") is True
        )
    except json.JSONDecodeError:
        return False

def filter_event_delete_completed(json_str):
    """
    Verifica se no JSON tem 'name': 'event_delete_completed' e 'value': True
    """
    try:
        json_data = json.loads(json_str)
        return (
            json_data.get("name") == "event_delete_completed"
            and json_data.get("value") is True
        )
    except json.JSONDecodeError:
        return False

# -------------------------------------------------------------------
# Funções para ler/armazenar estatísticas no DB
def get_last_stats_from_db():
    """
    Retorna o último stats_data (JSON) armazenado na tabela Statisticas, 
    ordenado por "createdAt" DESC. Se não existir, retorna None.
    """
    query = """
    SELECT stats_data
    FROM "Statisticas"
    ORDER BY "createdAt" DESC
    LIMIT 1
    """
    df = pd.read_sql(query, engine)
    
    if len(df) == 0:
        return None
    else:
        # Se vier string JSON em vez de dict
        last_stats = df['stats_data'][0]
        if isinstance(last_stats, str):
            last_stats = json.loads(last_stats)
        return last_stats
def filter_feedback_value(json_str):
    try:
        json_data = json.loads(json_str)  # Converte string JSON para dicionário
        # Verifica se existe a chave 'feedback' e retorna o 'value'
        if json_data.get("name") == "feedback":
            return json_data.get("value", None)  # Retorna o 'value' ou None se não existir
        return None
    except json.JSONDecodeError:
        return None  # Retorna None em caso de erro ao decodificar o JSON
        
def extract_feedback_number(value):
    try:
        # Procura por números inteiros de 1 a 5
        match = re.search(r'\b[1-5]\b', str(value))
        if match:
            return int(match.group())  # Retorna o número encontrado como inteiro
        return None  # Retorna None se nenhum número válido for encontrado
    except:
        return None
def insert_stats_in_db(stats_dict):
    """
    Insere o dicionário de estatísticas em formato JSON no banco.
    """
    assistant_id = "20241028-210249-mild-cream"  # fixo ou busque de outra forma
    current_time = datetime.datetime.utcnow()

    data_to_insert = {
        'assistant_id': [assistant_id],
        'stats_data': [stats_dict],
        'createdAt': [current_time],
        'updatedAt': [current_time]
    }
    df_to_insert = pd.DataFrame(data_to_insert)
    
    df_to_insert.to_sql(
        'Statisticas',
        con=engine,
        if_exists='append',
        index=False,
        dtype={'stats_data': JSONB}  # informa que stats_data é JSONB
    )
def calculate_duration(df):
    # Certifique-se de que o DataFrame está ordenado por sender_id e timestamp
    df = df.sort_values(by=['sender_id', 'timestamp'])

    # Agrupa pelo sender_id e calcula o primeiro e o último timestamp
    grouped = df.groupby('sender_id')

    durations = []
    for sender_id, group in grouped:
        first_timestamp = group['timestamp'].iloc[0]  # Primeiro timestamp
        last_timestamp = group['timestamp'].iloc[-1]  # Último timestamp
        duration = last_timestamp - first_timestamp  # Diferença em segundos

        durations.append({
            'sender_id': sender_id,
            'start_time': first_timestamp,
            'end_time': last_timestamp,
            'duration_seconds': duration
        })

    # Retorna um novo DataFrame com os resultados
    result_df = pd.DataFrame(durations)
    return result_df

def calculate_average_duration(df):
    # Calcula a duração total e a média
    average_duration = df['duration_seconds'].mean()
    return average_duration

def calculate_engagement(data):
    # Keys to exclude from the sum
    exclude_keys = {'action_transferir_atendente', 'login_sucess', 'novas_conversas', 'duration_cnvs'}
    
    # Sum the values of keys that are not in the exclude list
    total_sum = sum(value for key, value in data.items() if key not in exclude_keys)
    
    # Get the value of 'novas_conversas' to use as the divisor
    novas_conversas = data.get('novas_conversas', 1)  # Use 1 to avoid division by zero if not present
    
    # Calculate the result
    result = total_sum / novas_conversas if novas_conversas != 0 else 0
    
    return result
# -------------------------------------------------------------------
# Função principal: faz a leitura de "events", gera estatísticas e compara
def main():
    print("Iniciando execução...")

    # Ler tabela 'events' do DB
    df_table = pd.read_sql_table('events', engine)

    # 1) Exemplo: contagem de sender_id
    df_table_unique_sender_id = df_table['sender_id'].nunique()

    # 2) Filtrar actions
    actions = [
        'action_transferir_atendente',
        'action_ticket_receita',
        'action_provide_price_and_reset_slot',
        'action_confirm_appointment'
    ]
    df_table_actions = df_table.loc[df_table['action_name'].isin(actions)]
    df_table_actions = df_table_actions.drop(
        columns=['type_name','timestamp','intent_name','data']
    )
    df_table_actions = df_table_actions['action_name'].value_counts()

    # 3) Extrair utter_action
    df_table['utter_action'] = df_table['data'].apply(extract_utter_action)

    # 4) Filtrar utter_faq
    filtered_df2 = df_table[
        df_table['utter_action'].str.startswith('utter_faq/', na=False)
    ]
    df_filter = filtered_df2.loc[filtered_df2['intent_name'] == 'faq']
    df_filter2 = df_filter.drop_duplicates(subset=["sender_id", "utter_action"])
    df_filter2 = df_filter2.drop(
        columns=['data','type_name','action_name','intent_name','timestamp']
    )
    df_filter2['utter_action'] = (
        df_filter2['utter_action']
        .fillna("")
        .str.replace(r'^utter_faq/', '', regex=True)
    )
    df_filter2 = df_filter2['utter_action'].value_counts()

    # 5) Filtrar login_sucess, event_completed etc. 
    df_table['is_login_success_true'] = df_table['data'].apply(filter_login_success)
    df_table['is_event_complete_true'] = df_table['data'].apply(filter_event_completed)
    df_table['is_modify_true'] = df_table['data'].apply(filter_event_modify_completed)
    df_table['is_delete_true'] = df_table['data'].apply(filter_event_delete_completed)
    df_table['feedback_value']=df_table['data'].apply(filter_feedback_value)
    df_table['feedback_number'] = df_table['feedback_value'].apply(extract_feedback_number)

    df_table_login = df_table[df_table['is_login_success_true']]
    df_table_event = df_table[df_table['is_event_complete_true']]
    df_table_modify = df_table[df_table['is_modify_true']]
    df_table_delete = df_table[df_table['is_delete_true']]

    df_table_final = pd.concat([df_table_login,df_table_event,df_table_modify,df_table_delete])
    df_table_final = df_table_final.drop(
        columns=['type_name','timestamp','intent_name','data',
                 'is_login_success_true','is_event_complete_true',
                 'is_modify_true','is_delete_true','utter_action']
    )

    df_table_final_concluded = pd.concat([df_table_final, df_table_actions])
    # Se df_table_actions era Series, concatenar com DataFrame vira meio bagunçado;
    # mas segue a sua lógica original:
    df_table_final_concluded['action_name'].value_counts()

    df_counts_actions = df_table_final_concluded['action_name'].value_counts()

    # 6) Concat estatísticas: contagens + filter2 + table_actions
    df_statistics_final = pd.concat([df_counts_actions, df_filter2, df_table_actions])
    print(df_table_actions)
  
    # 7) Converter para dict e adicionar "novas_conversas",duration,'feedback',engagement
    mean_feedback = df_table['feedback_number'].mean()

    stats_json = df_statistics_final.to_dict()
    stats_json["novas_conversas"] = df_table_unique_sender_id
    result = calculate_duration(df_table)
    average_duration_conversation= calculate_average_duration(result)
    stats_json['duration_cnvs'] = average_duration_conversation
    engagement = calculate_engagement(stats_json)
    stats_json['engagement']= engagement
    stats_json['feedback_mean']=mean_feedback

    # 8) Comparar com último stats salvo no DB
    last_stats = get_last_stats_from_db()

    if last_stats == stats_json:
        print("Nenhuma mudança nos dados. Não será inserido novo registro.")
    else:
        print("Há mudança nos dados. Inserindo no banco...")
        insert_stats_in_db(stats_json)
        print("Dados inseridos com sucesso!")


# -------------------------------------------------------------------
# Agendar para rodar a cada 10 segundos
if __name__ == "__main__":
    schedule.every(10).seconds.do(main)

    while True:
        schedule.run_pending()
        time.sleep(1)
