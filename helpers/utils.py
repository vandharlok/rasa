import random
import string
import pytz
from typing import Optional
from rasa_sdk.executor import CollectingDispatcher,Tracker
from typing import Dict, Text, Any, List, Tuple
import logging 
import requests
from datetime import datetime, timedelta
from helpers.dates_utils import normalize_date,parse_event_time, format_time, get_current_datetime,calculate_start_hour

from typing import List, Dict, Any
import requests
import logging

# Configuração do logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

START_HOUR = 7
END_HOUR = 18
MAX_SLOTS = 5
TIMEZONE = 'America/Sao_Paulo'

def confirm_user(cpf_user):
    url = f"http://localhost:3020/usuario/consulta/{cpf_user}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            logger.info(f"User validation successful")
        else:
            logger.warning(f"User validation failed with status code {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to user validation service for CPF {cpf_user}: {e}")
        return False
        
def validate_cpf_value(slot_value: Any,
        dispatcher: CollectingDispatcher,
        ) -> Dict[Text,Any]:
    
    slot_value = ''.join(filter(str.isdigit, slot_value))

    if len(slot_value) != 11:
        dispatcher.utter_message(text="CPF deve conter 11 digitos")
        return {"cpf": None}

    if(slot_value):
        return {"cpf": slot_value}
    else:
        dispatcher.utter_message(text="CPF Inválido")
        return {"cpf": None}

        
def validate_cpf_bd(
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        ) -> Dict[Text,Any]:
    try:
        if confirm_user(slot_value):  
            return {"cpf" : slot_value}
        else:
            dispatcher.utter_message("Parece que você não está cadastrado.")
            logger.warning(f"CPF validation failed for {slot_value}. CPF not found.")
            return {"cpf" : None,}
    except Exception as e:
        dispatcher.utter_message("Não conseguimos validar seu CPF")
        logger.error(f"Error during CPF validation for {slot_value}: {str(e)}")
        return {"cpf" : None}
    
    
def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string



def get_event_id_from_cpf(cpf_user: str) -> List[Dict[str, Any]]:
    """
    Recupera detalhes de agendamento associados ao CPF fornecido.

    Retorna:
        List[Dict[str, Any]]: Uma lista de dicionários de agendamento contendo
                              'codAgendamento', 'medicoId', 'dataInicial' e 'dataFinal'.
    """
    url_get = f"http://localhost:3020/agendamentos/{cpf_user}"
    agendamentos = []

    try:
        response_get = requests.get(url_get, timeout=10)
        response_get.raise_for_status()

        data = response_get.json()
        events = data.get('agendamentos', [])

        if not events:
            logger.info(f"Nenhum evento encontrado para o CPF: {cpf_user}")
            return agendamentos  # Retorna lista vazia

        # Extrair codAgendamento, medicoId, dataInicial e dataFinal
        agendamentos = [
            {
                'codAgendamento': event['codAgendamento'],
                'medicoId': event['medicoId'],
                'dataInicial': event['dataInicial'],
                'dataFinal': event['dataFinal']
            }
            for event in events
            if (
                isinstance(event, dict) and
                'codAgendamento' in event and
                'medicoId' in event and
                'dataInicial' in event and
                'dataFinal' in event
            )
        ]

        if not agendamentos:
            logger.info(f"Eventos encontrados para o CPF {cpf_user}, mas faltam campos obrigatórios.")
            return agendamentos  # Retorna lista vazia

        logger.info(f"Agendamento(s) recuperado(s) para CPF {cpf_user}: {agendamentos}")

        # Sempre retornar uma lista, mesmo que contenha apenas um agendamento
        return agendamentos

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Falha na requisição HTTP para o CPF {cpf_user}: {req_err}")
    except ValueError as json_err:
        logger.error(f"Falha na decodificação JSON para o CPF {cpf_user}: {json_err}")
    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado para o CPF {cpf_user}: {e}")

    # Em caso de erros, retornar uma lista vazia
    return []


#funcao que faz a busca dos proximos 5 horarios livres, comecando a partir das 7 horas, com intervalo de 1 hora


def modify_event(medicoId,event_id: str, start_time: str, end_time: str) -> bool:
    url = f"http://localhost:3020/agendamento/atualizar/{event_id}"  
    data = {
        "dataInicial": start_time,
        "dataFinal": end_time,
        "medicoId": medicoId
    }
    
    try:
        response = requests.put(url, json=data)
        response.raise_for_status()  
        

        logger.info(f'Evento atualizado com sucesso: {response.json()}') 
        return True

    except requests.exceptions.RequestException as error:
        logger.error(f'Ocorreu um erro ao atualizar o evento {event_id}: {error}')
        return False


def fetch_events(api_url: str, dispatcher: CollectingDispatcher) -> Optional[List[dict]]:
    """
    Obtém os agendamentos da API.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        events_result = response.json()
        logger.debug("Agendamentos obtidos com sucesso.")

        if 'agendamentos' in events_result:
            return events_result['agendamentos']
        elif 'message' in events_result and events_result['message'] == "Nenhum consulta encontrado para este Médico.":
            # Nenhum agendamento encontrado, tratar como lista vazia
            logger.info("Nenhum agendamento encontrado para o médico. Todos os horários estão disponíveis.")
            return []
        else:
            dispatcher.utter_message(text="Resposta inesperada da API.")
            logger.warning(f"Resposta inesperada da API: {events_result}")
            return []
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            # Assumindo que 404 significa "nenhum agendamento encontrado"
            logger.info("Nenhum agendamento encontrado para o médico (404). Tratando como lista vazia.")
            return []
        else:
            logger.error(f"Erro HTTP ao recuperar agendamentos: {http_err}")
            dispatcher.utter_message(text="Erro ao recuperar agendamentos do calendário.")
            return None
    except Exception as e:
        logger.error(f"Erro ao recuperar agendamentos: {e}")
        dispatcher.utter_message(text="Erro ao recuperar agendamentos do calendário.")
        return None

def is_time_free(check_time: datetime, events: List[dict], timezone: pytz.timezone) -> bool:
    """
    Verifica se um horário específico está livre, dado a lista de eventos.
    """
    for event in events:
        event_start, event_end = parse_event_time(event, timezone)
        if event_start <= check_time < event_end:
            return False
    return True




def generate_all_possible_slots(date: datetime) -> List[str]:
    """
    Gera todos os horários possíveis para um determinado dia.
    """
    return [f"{hour}:00" for hour in range(START_HOUR, END_HOUR)]

def find_available_slots(
    date: datetime, 
    events: List[dict], 
    dispatcher: CollectingDispatcher, 
    num_slots_needed: int = MAX_SLOTS
) -> List[str]:
    """
    Encontra horários disponíveis para a data especificada.
    """
    available_slots = []
    timezone = pytz.timezone(TIMEZONE)
    current_datetime = get_current_datetime(timezone)
    current_date = current_datetime.date()
    date_only = date.date()

    # Ajusta a data se for uma data passada
    if date_only < current_date:
        date = current_datetime
        date_only = date.date()

    while len(available_slots) < num_slots_needed:
        daily_slots = []
        # Determina a hora de início
        start_hour = calculate_start_hour(date, current_datetime, current_date)
        if start_hour >= END_HOUR:
            date += timedelta(days=1)
            date_only = date.date()
            continue  # Próximo dia

        for hour in range(start_hour, END_HOUR):
            if len(available_slots) >= num_slots_needed:
                break
            check_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            if is_time_free(check_time, events, timezone):
                daily_slots.append(format_time(check_time))

        if daily_slots:
            available_slots.extend(daily_slots[:num_slots_needed - len(available_slots)])
        else:
            dispatcher.utter_message(text=f"Não temos horário para {date.strftime('%d/%m')}. Verificando os próximos horários disponíveis.")

        date += timedelta(days=1)  # Próximo dia
        date_only = date.date()

    return available_slots

def check_availability(
    date: datetime, 
    dispatcher: CollectingDispatcher, 
    api_url: str,
    num_slots_needed: int = MAX_SLOTS
) -> Tuple[bool, List[str]]:
    """
    Verifica a disponibilidade de horários a partir da data especificada.

    Retorna:
        - bool: True se houver horários disponíveis, False caso contrário.
        - List[str]: Lista de horários disponíveis.
    """
    events = fetch_events(api_url, dispatcher)
    if events is None:
        return False, []

    # Se events estiver vazio, significa que não há agendamentos, então todos os horários estão disponíveis
    if not events:
        logger.info("Nenhum agendamento encontrado. Todos os horários estão disponíveis.")
        available_slots = generate_all_possible_slots(date)
        return True, available_slots

    available_slots = find_available_slots(date, events, dispatcher, num_slots_needed)

    if available_slots:
        return True, available_slots
    else:
        logger.warning("Nenhum horário disponível encontrado após verificar múltiplos dias.")
        return False, []

def find_next_free_slots(api_url: str, dispatcher: CollectingDispatcher, max_slots: int = MAX_SLOTS) -> List[str]:
    """
    Encontra os próximos horários livres a partir de amanhã às START_HOUR h.
    """
    timezone = pytz.timezone(TIMEZONE)
    current_datetime = get_current_datetime(timezone)
    # Define start time as tomorrow at START_HOUR
    start_time = (current_datetime + timedelta(days=1)).replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
    free_slots = []

    while len(free_slots) < max_slots:
        start_of_day = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        last_end_time = start_of_day + timedelta(hours=START_HOUR)

        try:
            # Chamada da API com parâmetros corretos
            response = requests.get(api_url + f'?dataInicial={start_of_day.isoformat()}&dataFinal={end_of_day.isoformat()}')
            response.raise_for_status()
            events_result = response.json()
            # Corrigir para 'agendamentos'
            events = events_result.get('agendamentos', [])
            logger.debug(f"Agendamentos obtidos para o dia {start_of_day.strftime('%d/%m/%Y')}.")
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                # Assumindo que 404 significa "nenhum agendamento encontrado"
                logger.info(f"Nenhum agendamento encontrado para o dia {start_of_day.strftime('%d/%m/%Y')} (404). Tratando como todos os horários disponíveis.")
                events = []
            else:
                logger.error(f"Erro HTTP ao buscar agendamentos: {http_err}")
                dispatcher.utter_message(text="Erro ao buscar agendamentos para os próximos horários disponíveis.")
                break
        except Exception as e:
            logger.error(f"Falha ao buscar agendamentos: {str(e)}")
            dispatcher.utter_message(text="Erro ao buscar agendamentos para os próximos horários disponíveis.")
            break

        if not events:
            # Se não há agendamentos, todos os horários estão disponíveis
            while last_end_time < end_of_day and last_end_time.hour < END_HOUR and len(free_slots) < max_slots:
                free_slots.append(format_time(last_end_time))
                last_end_time += timedelta(hours=1)
        else:
            for event in events:
                start_event, end_event = parse_event_time(event, timezone)
                while last_end_time < start_event and last_end_time.hour < END_HOUR and len(free_slots) < max_slots:
                    free_slots.append(format_time(last_end_time))
                    last_end_time += timedelta(hours=1)
                last_end_time = max(last_end_time, end_event)

            # Após processar todos eventos, adicionar horários após o último evento
            while last_end_time < end_of_day and last_end_time.hour < END_HOUR and len(free_slots) < max_slots:
                free_slots.append(format_time(last_end_time))
                last_end_time += timedelta(hours=1)

        start_time = end_of_day

    return free_slots[:max_slots]

def handle_unavailable_time(adjusted_date: datetime, dispatcher: CollectingDispatcher, api_url: str, num_slots_needed: int = MAX_SLOTS) -> Dict[Text, Any]:
    """
    Lida com situações onde o horário desejado não está disponível, buscando novos horários.
    """
    is_available, available_times = check_availability(adjusted_date, dispatcher, api_url, num_slots_needed)
    if is_available:
        slots_message = ', '.join(available_times)
        dispatcher.utter_message(text=f"Próximos horários disponíveis: {slots_message}")
    else:
        dispatcher.utter_message(text="Não há horários disponíveis.")
    return {"time": None}

def validate_time_def(slot_value: str, dispatcher: CollectingDispatcher, tracker: Tracker) -> Dict[Text, Any]:
    """
    Valida o horário fornecido pelo usuário e interage com o dispatcher para informar a disponibilidade.
    """
    medicoId = tracker.get_slot('medicoId')
    api_url = f"http://localhost:3020/agendamentos/medico/{medicoId}"
    normalized_date = normalize_date(slot_value, dispatcher)

    if not normalized_date:
        logger.error("Falha ao normalizar a data.")
        dispatcher.utter_message(text="Data fornecida é inválida.")
        return {"time": None}

    timezone = pytz.timezone(TIMEZONE)
    current_datetime = get_current_datetime(timezone)
    current_date = current_datetime.date()
    normalized_date_only = normalized_date.date()

    if normalized_date_only < current_date:
        # Data passada: ajustar para próxima hora
        adjusted_date = current_datetime + timedelta(hours=1)
        return handle_unavailable_time(adjusted_date, dispatcher, api_url)

    elif normalized_date_only == current_date:
        if normalized_date < current_datetime:
            # Horário passado hoje: ajustar para próxima hora
            dispatcher.utter_message(text="Vou te mostrar os próximos horários disponíveis:")
            adjusted_date = current_datetime + timedelta(hours=1)
            return handle_unavailable_time(adjusted_date, dispatcher, api_url)
        else:
            # Horário futuro hoje: verificar disponibilidade específica
            check_time_iso = normalized_date.isoformat()
            events = fetch_events(api_url, dispatcher)
            if events is None:
                return {"time": None}

            is_available = not any(
                event['dataInicial'] <= check_time_iso < event['dataFinal'] for event in events
            )

            if is_available:
                dispatcher.utter_message(
                    f"{normalized_date.strftime('%d/%m/%Y %H:%M')} está disponível"
                )
                print(normalized_date.strftime('%d/%m/%Y %H:%M'))
                return {"time": normalized_date.isoformat(), "form_completed": True}
            else:
                dispatcher.utter_message(
                    text="Infelizmente, esse horário não está disponível. Vou te mostrar outros horários próximos."
                )
                dispatcher.utter_message(
                    f"{normalized_date.strftime('%d/%m/%Y %H:%M')} nao está disponível"
                )
                
                print(normalized_date.strftime('%d/%m/%Y %H:%M'))
                adjusted_date = current_datetime + timedelta(hours=1)
                return handle_unavailable_time(adjusted_date, dispatcher, api_url)

    else:
        # Data futura
        if normalized_date.hour == 0 and normalized_date.minute == 0:
            # Apenas a data foi fornecida: mostrar horários disponíveis para o dia
            is_available, available_times = check_availability(normalized_date, dispatcher, api_url)
            if is_available:
                slots_message = ', '.join(available_times)
                dispatcher.utter_message(
                    text=f"Próximos horários disponíveis em {normalized_date.strftime('%d/%m')}: {slots_message}"
                )
            else:
                dispatcher.utter_message(
                    text=f"Não há horários disponíveis em {normalized_date.strftime('%d/%m')}."
                )
            return {"time": None}
        else:
            # Horário específico em data futura: verificar disponibilidade
            check_time_iso = normalized_date.isoformat()
            events = fetch_events(api_url, dispatcher)
            if events is None:
                return {"time": None}

            is_available = not any(
                event['dataInicial'] <= check_time_iso < event['dataFinal'] for event in events
            )

            if is_available:
                dispatcher.utter_message(
                    f"{normalized_date.strftime('%d/%m/%Y %H:%M')} está disponível"
                )
                return {"time": normalized_date.isoformat(), "form_completed": True}
            else:
                dispatcher.utter_message(
                    text="Infelizmente, esse horário não está disponível. Vou te mostrar outros horários próximos."
                )
                return handle_unavailable_time(normalized_date, dispatcher, api_url)

    # Retorno padrão
    return {"time": None}