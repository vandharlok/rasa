import dateparser
import logging 
from rasa_sdk.executor import CollectingDispatcher
from typing import Optional
from datetime import datetime
import pytz
from typing import Tuple


START_HOUR = 7
END_HOUR = 18
MAX_SLOTS = 5
TIMEZONE = 'America/Sao_Paulo'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def normalize_date(slot_value: str, dispatcher: CollectingDispatcher) -> Optional[datetime]:
    """
    Normaliza a string de entrada para um objeto datetime com fuso horário.
    """
    target_date = dateparser.parse(
        slot_value,
        settings={
            'TIMEZONE': TIMEZONE,
            'RETURN_AS_TIMEZONE_AWARE': True
        }
    )
    if target_date is None:
        dispatcher.utter_message(text="Não consegui entender a data: " + slot_value)
        logger.info("Erro ao analisar a data.")
        return None
    return target_date


def parse_event_time(event: dict, timezone: pytz.timezone) -> Tuple[datetime, datetime]:
    """
    Analisa e converte os tempos de início e fim de um evento para o fuso horário especificado.
    """
    event_start = datetime.fromisoformat(event['dataInicial'].replace("Z", "+00:00")).astimezone(timezone)
    event_end = datetime.fromisoformat(event['dataFinal'].replace("Z", "+00:00")).astimezone(timezone)
    return event_start, event_end



def format_time(check_time: datetime) -> str:
    """
    Formata o horário para exibição.
    """
    return check_time.strftime('%d/%m %H:%M')



def get_current_datetime(timezone: pytz.timezone) -> datetime:
    """
    Obtém o datetime atual com o fuso horário especificado.
    """
    return datetime.now(tz=timezone)



def calculate_start_hour(date: datetime, current_datetime: datetime, current_date: datetime.date) -> int:
    """
    Calcula a hora de início para buscar horários disponíveis.
    """
    if date.date() == current_date:
        return max(current_datetime.hour + 1, START_HOUR)
    return START_HOUR


def format_date(date_str: str) -> str:
    """
    Formata uma string de data no formato ISO 8601 para uma string legível em português.

    Args:
        date_str (str): Data no formato ISO 8601 (ex: '2024-10-22T09:00:00-03:00').

    Returns:
        str: Data formatada (ex: '22 de Outubro de 2024 às 09:00').
    """
    # Lista de meses em português
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    try:
        # Parse da string de data no formato ISO 8601
        data_inicial = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        logger.error(f"Formato de data inválido: {date_str}")
        raise ValueError("Formato de data inválido")

    dia = data_inicial.day
    mes = meses[data_inicial.month - 1]
    ano = data_inicial.year
    hora = data_inicial.strftime('%H:%M')

    # Formatação da data
    data_formatada = f"{dia} de {mes} de {ano} às {hora}"
    return data_formatada