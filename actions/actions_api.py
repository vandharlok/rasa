
from helpers.utils import generate_random_string,find_next_free_slots,modify_event
from rasa_sdk.events import FollowupAction
from datetime import timedelta
from rasa_sdk import Action, Tracker
from typing import Dict, Text, Any, List
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker
from rasa_sdk.events import  SlotSet, AllSlotsReset, ConversationPaused, ConversationResumed

from rasa_sdk.events import EventType

import requests
import logging 
import dateparser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ActionSalvarCadastro(Action):
    def name(self) -> Text:
        return "action_salvar_cadastro"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        nome = tracker.get_slot("nome")
        email = tracker.get_slot("email")
        cpf = tracker.get_slot("cpf")
        telefone = tracker.get_slot("telefone")

        url = "http://localhost:3020/usuario/cadastro"
        data = {
            "name": nome,
            "email": email,
            "cpf": cpf,
            "phoneNumber": telefone,
            "adminId": 1,
            "observation":"1"
        }
        try:
            response = requests.post(url, json=data)
            if 200 <= response.status_code < 300:
                logger.info(f"Usuário de email : {email} registrado com sucesso.")
                return [SlotSet("login_sucess", True)]
            
            else:
                dispatcher.utter_message(text="Falha ao cadastrar o usuário. Tente novamente.")
                logger.warning(f"Falha ao cadastrar usuario: {email}. Status code: {response.status_code}")
                return [SlotSet("login_sucess", False),AllSlotsReset()]
        except requests.exceptions.RequestException as e:
            logger.error("Erro de conexão com o serviço de registro: %s", str(e))
            return [SlotSet("login_sucess", False),AllSlotsReset()]

class ValidateAndAddEvent(Action):
    def name(self) -> Text:
        return "action_add_event"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[EventType]:

        time_str = tracker.get_slot('time')
        cpf_user = tracker.get_slot('cpf')
        medico_id = tracker.get_slot('medicoId')
        nome_user = tracker.get_slot('nome')  # Assuming you have user's name in a slot

        if not medico_id:
            dispatcher.utter_message(text="Desculpe, não identifiquei o profissional para agendar a consulta.")
            return []

        target_date = dateparser.parse(time_str, settings={'TIMEZONE': 'America/Sao_Paulo', 'RETURN_AS_TIMEZONE_AWARE': True})
        if not target_date:
            dispatcher.utter_message(text="Formato de data e hora incorreto. Por favor, tente novamente.")
            return [SlotSet("time", None), FollowupAction("action_listen")]

        new_end_time = target_date + timedelta(hours=1)
        string_length = 10
        random_string = generate_random_string(string_length)

        start_time = target_date.isoformat()
        new_end_time_str = new_end_time.isoformat()

        try:
            url = "http://localhost:3020/agendamento/cadastrar"
            data = {
                "codAgendamento": random_string,
                "cpfUser": cpf_user,
                "nomeUser": "paciente",
                "dataInicial": start_time,
                "dataFinal": new_end_time_str,
                "medicoId": medico_id
            }
            response = requests.post(url, json=data)
            if 200 <= response.status_code < 300:
                dispatcher.utter_message(text="Consulta marcada!")
                logger.info("Appointment created")  
                return [
                    SlotSet("form_completed", False),
                    SlotSet("time", None),
                    SlotSet("event_completed", True),
                    SlotSet("event_id", None),
                    SlotSet("cpf", None),
                    SlotSet("especialista", None),
                    SlotSet("profissional", None),
                    SlotSet("medicoId", None),
                ]
            else:
                dispatcher.utter_message(text="Ocorreu um problema ao realizarmos sua consulta, por favor, tente novamente ou peça por um atendimento humano!")
                logger.warning("Fail to appoint.")
                return [SlotSet("time", None), SlotSet("cpf", None),SlotSet("event_completed", False)]
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text="Erro ao conectar ao serviço de cadastro.")
            logger.error("Error to connect to service")
            return [SlotSet("time", None), SlotSet("event_id", None), SlotSet("cpf", None),SlotSet("event_completed", False)]
        except Exception as e:
            logger.error("Error to connect to service")
            dispatcher.utter_message(text=f"Não foi possível adicionar o evento: {e}")
            return [SlotSet("time", None), SlotSet("event_id", None), SlotSet("cpf", None),SlotSet("event_completed", False)]
        
class ActionFindFreeSlots(Action):
    def name(self) -> Text:
        return "action_find_free_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        medicoId=tracker.get_slot('medicoId')
        api_url = f"http://localhost:3020/agendamentos/medico/{medicoId}"
        free_slots = find_next_free_slots(api_url,dispatcher)

        if free_slots:
            dispatcher.utter_message(text=f"Os próximos horários disponíveis são: {', '.join(free_slots)}")
            return [SlotSet("free_slots", free_slots)]
        else:
            dispatcher.utter_message(text="Nenhum horário disponível dentro do intervalo especificado.")
            return [SlotSet("free_slots", [])]
        

           
class ModifyGoogleCalendarEvent(Action):
    def name(self) -> str:
        return "action_modify_event_form"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        new_start_time_str = tracker.get_slot('time')
        event_id = tracker.get_slot("event_id")
        medicoId= tracker.get_slot("medicoId")
        if not event_id:
            dispatcher.utter_message(text="Algo deu errado, tente novamente, ou chame um atendente!")
            return []

        try:
            target_date = dateparser.parse(
                new_start_time_str,
                settings={
                    'TIMEZONE': 'America/Sao_Paulo',
                    'RETURN_AS_TIMEZONE_AWARE': True
                }
            )
            if not target_date:
                dispatcher.utter_message(text="Formato de data e hora incorreto. Por favor, tente novamente.")
                return [SlotSet("time", None), FollowupAction("action_listen")]

            new_end_time = target_date + timedelta(hours=1)
            new_start_time_str = target_date.isoformat()
            new_end_time_str = new_end_time.isoformat()

            
            if modify_event(medicoId,event_id, new_start_time_str, new_end_time_str):
                dispatcher.utter_message(text="Mudança de consulta concluída com sucesso!")
                return [
                    SlotSet("form_completed", False),
                    SlotSet("event_modify_completed", True),
                    SlotSet("cpf", None),
                    SlotSet("event_id", None),
                    SlotSet("time", None),
                    SlotSet("medicoId",None)
                ]
            else:
                dispatcher.utter_message(text="Não conseguimos mudar sua consulta de data!")
                return [
                    SlotSet("event_modify_completed", False),
                    SlotSet("cpf", None),
                    SlotSet("event_id", None),
                    SlotSet("time", None),
                    SlotSet("medicoId",None)

                ]

        except ValueError as e:
            dispatcher.utter_message(text=f"Erro ao processar as datas: {str(e)}")
            logger.error(f"Error processing dates: {e}")

        return [
            SlotSet("cpf", None),
            SlotSet("event_id", None),
            SlotSet("time", None),
            SlotSet("medicoId",None)

        ]
    
class ActionDeleteGoogleCalendarEvent(Action):
    def name(self):
        return "action_delete_event_form"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        
        cpf_user = tracker.get_slot('cpf')
        event_id= tracker.get_slot("event_id")        
        if not event_id:
            dispatcher.utter_message(text="Desculpe, não encontramos sua consulta")
            return [SlotSet("event_delete_completed", False), SlotSet("cpf", None)]

        
        url_delete = f"http://localhost:3020/agendamento/deletar/{event_id}"
        try:
            response_delete = requests.delete(url_delete)
            if 200 <= response_delete.status_code < 300:
                dispatcher.utter_message(text="Consulta cancelada com sucesso!")
                logger.info(f"Appointment {event_id} successfully cancelled.")
                return [SlotSet("event_delete_completed", True), SlotSet("cpf", None),SlotSet("event_id",None)]
            else:
                dispatcher.utter_message(text="Parece que não conseguimos cancelar sua consulta, tente mais tarde novamente.")
                logger.warning(f"Failed to delete event {event_id} from local database: {response_delete.status_code}")
                return [SlotSet("event_delete_completed", False), SlotSet("cpf", None),SlotSet("event_id",None)]
        except Exception as e:
            dispatcher.utter_message(text="Erro ao deletar a consulta, tente novamente mais tarde!")
            logger.error(f"Failed to communicate with local database for deleting event {event_id}: {str(e)}")
            return [SlotSet("event_delete_completed", False), SlotSet("cpf", None),SlotSet("event_id",None)]
            
        

