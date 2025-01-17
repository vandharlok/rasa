1. ValidateAndAddEvent
Nome da Ação: action_add_event
Descrição: Adiciona um evento ao Google Calendar e também registra o evento em um banco de dados local. A ação utiliza a função add_event para criar o evento no Google Calendar e faz uma requisição POST para armazenar os detalhes do evento no banco de dados.
Parâmetros:
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
tracker (Tracker): O tracker para rastrear o estado da conversa.
domain (Dict[Text, Any]): O domínio da conversa.
Retorno: Uma lista de eventos do Rasa SDK, incluindo SlotSet para limpar os slots e FollowupAction para continuar a conversa se necessário.
2. ActionFindFreeSlots
Nome da Ação: action_find_free_slots
Descrição: Busca os próximos horários livres no Google Calendar para agendamento. A ação utiliza a função find_next_free_slots para obter os horários disponíveis e retorna uma lista desses horários para o usuário.
Parâmetros:
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
tracker (Tracker): O tracker para rastrear o estado da conversa.
domain (Dict[Text, Any]): O domínio da conversa.
Retorno: Uma lista de eventos do Rasa SDK, incluindo SlotSet para armazenar os horários livres.
3. ModifyGoogleCalendarEvent
Nome da Ação: action_modify_google_calendar_event
Descrição: Modifica um evento existente no Google Calendar. A ação obtém o ID do evento a partir do CPF do usuário, valida a nova data e hora, e utiliza a função modify_event para atualizar o evento no Google Calendar e no banco de dados local.
Parâmetros:
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
tracker (Tracker): O tracker para rastrear o estado da conversa.
domain (Dict[Text, Any]): O domínio da conversa.
Retorno: Uma lista de eventos do Rasa SDK, incluindo SlotSet para limpar os slots e um feedback para o usuário.
4. ActionDeleteGoogleCalendarEvent
Nome da Ação: action_delete_google_calendar_event
Descrição: Exclui um evento existente no Google Calendar e no banco de dados local. A ação busca o ID do evento a partir do CPF do usuário e utiliza a API do Google Calendar para deletar o evento. Em seguida, remove o evento do banco de dados local.
Parâmetros:
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
tracker (Tracker): O tracker para rastrear o estado da conversa.
domain (Dict[Text, Any]): O domínio da conversa.
Retorno: Uma lista de eventos do Rasa SDK, incluindo SlotSet para limpar os slots e um feedback para o usuário.
5. find_next_free_slots
Descrição: Encontra os próximos horários livres para agendamento no Google Calendar. A função consulta o calendário a partir do horário atual e retorna uma lista com os próximos horários disponíveis até que o número máximo de horários livres seja atingido.
Parâmetros:
service: O serviço do Google Calendar autenticado.
max_slots (int, opcional): O número máximo de horários livres a serem retornados (padrão é 5).
Retorno:
List[str]: Uma lista de strings representando os próximos horários disponíveis.
6. add_event
Descrição: Adiciona um novo evento ao Google Calendar. A função cria um evento com um nome e horário fornecidos e retorna o ID do evento criado.
Parâmetros:
event_name (str): O nome do evento.
start_time (datetime): O horário de início do evento.
Retorno:
str: O ID do evento criado.
7. get_calendar_service
Descrição: Autentica e retorna o serviço do Google Calendar. A função carrega as credenciais salvas em um arquivo pickle ou realiza o processo de autenticação utilizando o OAuth2 se as credenciais não estiverem disponíveis ou expiradas.
Parâmetros: Nenhum.
Retorno:
service: O serviço do Google Calendar autenticado.
8. modify_event
Descrição: Modifica um evento existente no Google Calendar. A função utiliza o ID do evento para atualizar os horários de início e término no Google Calendar.
Parâmetros:
event_id (str): O ID do evento a ser modificado.
start_time (str): O novo horário de início do evento.
end_time (str): O novo horário de término do evento.
Retorno:
bool: Retorna True se a modificação for bem-sucedida, False caso contrário.
9. validate_time_def
Descrição: Valida o horário fornecido pelo usuário e verifica sua disponibilidade no Google Calendar. Se o horário estiver disponível, ele é retornado; caso contrário, a função oferece horários alternativos.
Parâmetros:
slot_value (str): O horário fornecido como string.
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
Retorno:
Dict[Text, Any]: Retorna um dicionário com o horário validado ou None se o horário não estiver disponível.
10. normalize_date
Descrição: Normaliza uma data fornecida em uma string para um objeto datetime, utilizando o fuso horário "America/Sao_Paulo".
Parâmetros:
slot_value (str): A data fornecida como string.
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
Retorno:
Optional[datetime]: Retorna a data normalizada ou None se a data não puder ser interpretada.
11. check_availability
Descrição: Verifica a disponibilidade de horários para uma data específica no Google Calendar. Retorna uma lista dos horários disponíveis para a data.
Parâmetros:
date (datetime): A data para a qual a disponibilidade deve ser verificada.
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
service: O serviço do Google Calendar autenticado.
Retorno:
Tuple[bool, List[str]]: Retorna True e uma lista de horários disponíveis se houver disponibilidade, ou False e uma lista vazia caso contrário.