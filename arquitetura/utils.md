1. confirm_user
Descrição: Verifica se o usuário com o CPF fornecido está registrado no sistema. Faz uma requisição GET para um serviço externo de consulta de usuário.
Parâmetros:
cpf_user (str): O CPF do usuário a ser verificado.
Retorno:
bool: Retorna True se o usuário for encontrado, False caso contrário.
2. validate_cpf_value
Descrição: Valida o formato e a integridade de um CPF fornecido, verificando se o CPF tem 11 dígitos e se os dígitos de verificação estão corretos.
Parâmetros:
slot_value (Any): O valor do CPF a ser validado.
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
Retorno:
Dict[Text, Any]: Retorna um dicionário com o CPF validado ou None se o CPF for inválido.
3. validate_cpf_bd
Descrição: Valida um CPF contra o banco de dados, verificando se o usuário correspondente está registrado. Faz uma chamada à função confirm_user.
Parâmetros:
slot_value (Any): O valor do CPF a ser validado.
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
Retorno:
Dict[Text, Any]: Retorna um dicionário com o CPF validado ou None se o CPF não for encontrado no banco de dados.
4. generate_random_string
Descrição: Gera uma string aleatória composta por letras maiúsculas, minúsculas e dígitos.
Parâmetros:
length (int): O comprimento da string aleatória a ser gerada.
Retorno:
str: A string aleatória gerada.
5. get_event_id_from_cpf
Descrição: Busca o ID do evento correspondente ao CPF do usuário. Faz uma requisição GET para um serviço externo que retorna os eventos do usuário.
Parâmetros:
cpf_user (str): O CPF do usuário.
Retorno:
Tuple[Optional[str], Optional[str]]: Retorna o ID do evento e None se encontrado, ou None e uma mensagem de erro caso contrário.
6. find_next_free_slots
Descrição: Encontra os próximos horários livres para agendamento, começando a partir das 7 horas da manhã, com intervalos de 1 hora, até encontrar o número máximo de horários disponíveis ou até as 18 horas.
Parâmetros:
api_url (str): A URL da API para buscar os eventos existentes.
max_slots (int, opcional): O número máximo de horários livres a serem retornados (padrão é 5).
Retorno:
List[str]: Uma lista dos próximos horários livres formatados como strings.
7. modify_event
Descrição: Modifica a data e o horário de um evento existente no sistema. Faz uma requisição PUT para um serviço externo para atualizar o evento.
Parâmetros:
event_id (str): O ID do evento a ser modificado.
start_time (str): O novo horário de início do evento.
end_time (str): O novo horário de término do evento.
Retorno:
bool: Retorna True se o evento for atualizado com sucesso, False em caso de erro.
8. normalize_date
Descrição: Normaliza uma data fornecida em uma string para um objeto datetime, usando o fuso horário "America/Sao_Paulo".
Parâmetros:
slot_value (str): A data fornecida como string.
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
Retorno:
Optional[datetime]: Retorna a data normalizada ou None se a data não puder ser interpretada.
9. check_availability
Descrição: Verifica a disponibilidade de horários para uma data específica. Retorna uma lista dos horários disponíveis.
Parâmetros:
date (datetime): A data para a qual a disponibilidade deve ser verificada.
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
api_url (str): A URL da API para buscar os eventos existentes.
Retorno:
Tuple[bool, List[str]]: Retorna True e uma lista de horários disponíveis se houver disponibilidade, ou False e uma lista vazia caso contrário.
10. validate_time_def
Descrição: Valida e normaliza um horário fornecido, verifica sua disponibilidade, e retorna os próximos horários disponíveis se o horário fornecido não estiver disponível. A função faz uso de outras funções como normalize_date e check_availability.
Parâmetros:
slot_value (str): O horário fornecido como string.
dispatcher (CollectingDispatcher): O dispatcher para enviar mensagens de resposta.
Retorno:
Dict[Text, Any]: Retorna um dicionário com o horário validado ou None se o horário não estiver disponível.
