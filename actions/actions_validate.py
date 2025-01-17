from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from typing import Dict, Text, Any
from rasa_sdk.interfaces import Tracker
from rasa_sdk.types import DomainDict
from helpers.utils import validate_cpf_bd, validate_cpf_value,validate_time_def,get_event_id_from_cpf
import re
import logging 
import requests
import pytz
from helpers.dates_utils import normalize_date, parse_event_time

TIMEZONE = 'America/Sao_Paulo'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ValidateNome(FormValidationAction):
    def name(self):
        return "validate_cadastro_form"

    def validate_nome(
            self, 
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],     
            ) -> Dict[Text, Any]:
            # Expressão regular ajustada para aceitar acentos
            if not re.match(r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$', slot_value):
                dispatcher.utter_message(text="O nome deve conter apenas letras.")
                return {"nome": None}
            elif len(slot_value) <= 2:
                dispatcher.utter_message(text="O nome deve ter mais de 2 caracteres.")
                return {"nome": None}
            else:
                return {"nome": slot_value}
        
    def validate_cpf(
            self, 
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict
            ) -> Dict[Text, Any]:
        return validate_cpf_value(slot_value, dispatcher)   
    
    
    def validate_telefone(
        self, 
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
        ) -> Dict[Text, Any]:
        
        pattern = re.compile(r'^\(\d{2}\) \d{5}-\d{4}$')
        
        if pattern.match(slot_value):
            logger.info("Telefone validado com sucesso.")
            return {"telefone": slot_value}
        else:
            dispatcher.utter_message(text="O telefone deve estar no formato (00) 00000-0000.")
            return {"telefone": None}
        
        
    def validate_email(
        self, 
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,     
        ) -> Dict[Text, Any]:
        # Expressão regular para validar formato de e-mail
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if re.match(email_pattern, slot_value):
            logger.info("email validated")
            return {"email": slot_value}
        else:
            dispatcher.utter_message(text="Insira um endereço de e-mail válido.")
            return {"email": None}
        
        
        
class ValidateCPFActionDelete(FormValidationAction):
    def name(self):
        return "validate_delete_event_form"

    def validate_cpf(
        self, 
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,     
        ) -> Dict[Text,Any]:
        return validate_cpf_bd(slot_value,dispatcher)
    def validate_event_id(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict
    ) -> Dict[Text, Any]:
        """
        Valida a data selecionada pelo usuário, encontra a consulta correspondente
        e atribui o medicoId ao slot para exclusão.
        """
        # Obter a data selecionada no payload (exemplo: "14 de Novembro de 2024 às 09:00")
        selected_date = slot_value

        if not selected_date:
            dispatcher.utter_message(text="A data selecionada é inválida. Por favor, tente novamente.")
            return {"event_id": None, "medicoId": None}

        # Normalizar a data selecionada
        normalized_date = normalize_date(selected_date, dispatcher)
        if not normalized_date:
            # Mensagem já enviada pelo normalize_date
            return {"event_id": None, "medicoId": None}

        # Obter o CPF do usuário
        cpf_user = tracker.get_slot("cpf")
        if not cpf_user:
            dispatcher.utter_message(text="Desculpe, não recebi o CPF para validação.")
            return {"event_id": None, "medicoId": None}

        # Obter agendamentos com base no CPF
        agendamentos = get_event_id_from_cpf(cpf_user)
        if not agendamentos:
            dispatcher.utter_message(text="Nenhum agendamento foi encontrado para este CPF.")
            return {"event_id": None, "medicoId": None}

        # Comparar a data normalizada com os agendamentos
        timezone = pytz.timezone(TIMEZONE)
        for agendamento in agendamentos:
            try:
                event_start, _ = parse_event_time(agendamento, timezone)
                if event_start == normalized_date:
                    # Data válida, retornar event_id e medicoId
                    return {
                        "event_id": agendamento["codAgendamento"],
                        "medicoId": agendamento["medicoId"],
                    }
            except Exception as e:
                logger.error(f"Erro ao processar agendamento: {e}")
                continue

        # Caso não encontre correspondência
        dispatcher.utter_message(text="A data selecionada não corresponde a nenhum agendamento existente.")
        return {"event_id": None, "medicoId": None}


        
class ValidateCPFActionConfirm(FormValidationAction):
    def name(self):
        return "validate_confirm_event_form"

    def validate_cpf(
        self, 
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,     
        ) -> Dict[Text,Any]:
        return validate_cpf_bd(slot_value,dispatcher)
 
class ValidateCPFActionModify(FormValidationAction):
    def name(self):
        return "validate_modify_event_form"

    def validate_cpf(
        self, 
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,     
        ) -> Dict[Text,Any]:
        return validate_cpf_bd(slot_value,dispatcher)
    
    def validate_time(self, 
                      slot_value: Any,
                      dispatcher: CollectingDispatcher,
                      tracker: Tracker,
                      domain: Dict) -> Dict[Text, Any]:
        return validate_time_def(slot_value, dispatcher,tracker)
    
    def validate_event_id(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict
    ) -> Dict[Text, Any]:
        """
        Valida a data selecionada pelo usuário, encontra a consulta correspondente
        e atribui o medicoId ao slot.
        """
        # Obter a data selecionada no payload (exemplo: "14 de Novembro de 2024 às 09:00")
        selected_date = slot_value

        if not selected_date:
            dispatcher.utter_message(text="A data selecionada é inválida. Por favor, tente novamente.")
            return {"event_id": None, "medicoId": None}

        # Normalizar a data selecionada
        normalized_date = normalize_date(selected_date, dispatcher)
        if not normalized_date:
            # Mensagem já enviada pelo normalize_date
            return {"event_id": None, "medicoId": None}

        # Obter o CPF do usuário
        cpf_user = tracker.get_slot("cpf")
        if not cpf_user:
            dispatcher.utter_message(text="Desculpe, não recebi o CPF para validação.")
            return {"event_id": None, "medicoId": None}

        # Obter agendamentos com base no CPF
        agendamentos = get_event_id_from_cpf(cpf_user)
        if not agendamentos:
            dispatcher.utter_message(text="Nenhum agendamento foi encontrado para este CPF.")
            return {"event_id": None, "medicoId": None}

        # Comparar a data normalizada com os agendamentos
        timezone = pytz.timezone(TIMEZONE)
        for agendamento in agendamentos:
            try:
                event_start, _ = parse_event_time(agendamento, timezone)
                if event_start == normalized_date:
                    # Data válida, retornar event_id e medicoId
                    return {
                        "event_id": agendamento["codAgendamento"],
                        "medicoId": agendamento["medicoId"],
                    }
            except Exception as e:
                logger.error(f"Erro ao processar agendamento: {e}")
                continue

        # Caso não encontre correspondência
        dispatcher.utter_message(text="A data selecionada não corresponde a nenhum agendamento existente.")
        return {"event_id": None, "medicoId": None}
   
#Valida o cpf do usuario, e o horario para marcar a consulta


class ValidateCPFActionEvent(FormValidationAction):
    def name(self):
        return "validate_event_form"

    def validate_cpf(
        self, 
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,     
        ) -> Dict[Text,Any]:
        return validate_cpf_bd(slot_value,dispatcher)
    
    def validate_time(self, 
                      slot_value: Any,
                      dispatcher: CollectingDispatcher,
                      tracker: Tracker,
                      domain: Dict) -> Dict[Text, Any]:
        return validate_time_def(slot_value, dispatcher,tracker)
    
    def validate_especialista(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        if not slot_value:
            dispatcher.utter_message(text="Desculpe, não recebi o especialista desejado. Por favor, escolha corretamente.")
            return {"especialista": None}


        # Fetch categories from API
        try:
            response = requests.get('http://localhost:3020/medicos')
            data = response.json()

            # Extract unique categories
            categorias = set()
            for item in data:
                categoria_nome = item['categoria']['nome'].lower()
                categorias.add(categoria_nome)

            if slot_value in categorias:
                return {"especialista": slot_value}
            else:
                dispatcher.utter_message(text="Desculpe, não entendi. Por favor, escolha uma opção válida para especialista.")
                return {"especialista": None}
        except Exception as e:
            dispatcher.utter_message(text="Desculpe, ocorreu um erro ao obter os especialistas. Tente novamente mais tarde.")
            return {"especialista": None}

    def validate_profissional(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        if not slot_value:
            dispatcher.utter_message(text="Desculpe, não recebi o profissional desejado. Por favor, escolha corretamente.")
            return {"profissional": None}
        
        slot_value = slot_value.lower()

        if slot_value == 'nenhum':
            return {"especialista": None, "profissional": None, "medicoId": None}

        especialista = tracker.get_slot('especialista')
        if not especialista:
            dispatcher.utter_message(text="Desculpe, não identifiquei o especialista escolhido. Por favor, escolha corretamente.")
            return {"profissional": None}

        # Fetch professionals from API filtered by especialista
        try:
            response = requests.get('http://localhost:3020/medicos')
            data = response.json()

            # Filter professionals based on 'especialista'
            profissionais = [
                item for item in data
                if item['categoria']['nome'].lower() == especialista
            ]

            # Map of professional names to their IDs
            profissionais_dict = {}
            for profissional in profissionais:
                nome = profissional['nome'].lower()
                id_medico = profissional['id']
                profissionais_dict[nome] = id_medico

            if slot_value in profissionais_dict:
                medico_id = profissionais_dict[slot_value]
                return {"profissional": slot_value, "medicoId": medico_id}
            else:
                dispatcher.utter_message(text="Desculpe, não entendi. Por favor, escolha uma opção válida para profissional.")
                return {"profissional": None}
        except Exception as e:
            dispatcher.utter_message(text="Desculpe, ocorreu um erro ao obter os profissionais. Tente novamente mais tarde.")
            return {"profissional": None}
        

class ValidateFeedbackForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_feedback_form"

    async def run(
        self, 
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,     
        ) -> Dict[Text,Any]:
        
        # Pega o valor atual do slot 'feedback'
        feedback = tracker.get_slot('feedback')
        
        # Valida o valor do feedback
        try:
            feedback = float(feedback)
        except ValueError:
            dispatcher.utter_message(text="Desculpe, não entendi. Por favor, insira uma nota entre 1 e 5.")
            return {"feedback", None}
        
        # Verifica se o feedback está entre 1 e 5
        if 1 <= feedback <= 5:
            return {"feedback", feedback}
        else:
            dispatcher.utter_message(text="Por favor, insira uma nota válida entre 1 e 5.")
            return {"feedback", None}