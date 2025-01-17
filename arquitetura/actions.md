1. ActionDefaultFallback
Nome da Ação: action_default_fallback
Descrição: Essa ação é acionada quando o Rasa não consegue entender a entrada do usuário. É configurada como uma ação de fallback no arquivo config.yml e é acionada quando a confiança do modelo cai abaixo de um certo limiar (atualmente configurado para 0,7). A ação reverte a última fala do usuário e envia uma mensagem pedindo para tentar novamente.
Retorno: UserUtteranceReverted()
2. ActionResetAll
Nome da Ação: action_reset_all
Descrição: Essa ação é responsável por reiniciar a conversa, zerando todos os slots preenchidos e reiniciando o tracker. Isso é útil para iniciar uma nova conversa sem qualquer contexto ou histórico anterior.
Retorno: Restarted(), AllSlotsReset()
3. ActionStoreFeedback
Nome da Ação: action_store_feedback
Descrição: Guarda o feedback fornecido pelo usuário. A ação captura o feedback do usuário (uma nota de 1 a 5), valida o valor e o armazena em um slot chamado feedback. Se o feedback for inválido, pede ao usuário para avaliar novamente.
Retorno: SlotSet("feedback", feedback), ou em caso de erro, SlotSet("feedback", None) e FollowupAction("action_listen").
4. ActionCustomFallback
Nome da Ação: action_custom_fallback
Descrição: Esta é uma ação de fallback customizada que conta quantas vezes o fallback foi acionado. Se o fallback for acionado quatro vezes seguidas, a ação mostra opções ao usuário e reseta a contagem. Caso contrário, pede ao usuário para reformular a pergunta.
Retorno: SlotSet("fallback_count", 0.0) ou SlotSet("fallback_count", fallback_count)
5. ActionSalvarCadastro
Nome da Ação: action_salvar_cadastro
Descrição: Esta ação é responsável por cadastrar o usuário em um banco de dados. Ela coleta os dados do usuário a partir dos slots (nome, email, cpf, telefone, data_nascimento) e faz uma requisição POST para a API de cadastro. Dependendo da resposta, marca o cadastro como bem-sucedido ou falho.
Retorno: SlotSet("login_sucess", True) em caso de sucesso, ou SlotSet("login_sucess", False) em caso de falha.
6. ValidateNome (FormValidationAction)
Nome da Ação: validate_cadastro_form
Descrição: Valida o nome fornecido pelo usuário em um formulário de cadastro. Verifica se o nome contém apenas letras e se tem mais de 2 caracteres. Se a validação falhar, a ação limpa o slot nome.
Retorno: {"nome": slot_value} ou {"nome": None}
7. ValidateCPFActionDelete (FormValidationAction)
Nome da Ação: validate_delete_event_form
Descrição: Valida o CPF fornecido pelo usuário antes de excluir um evento (consulta). A ação utiliza uma função de validação para verificar se o CPF é válido e está presente no banco de dados.
Retorno: Resultado da função validate_cpf_bd(slot_value, dispatcher)
8. ValidateCPFActionModify (FormValidationAction)
Nome da Ação: validate_modify_event_form
Descrição: Valida o CPF do usuário e o novo horário fornecido para remarcar uma consulta. A ação utiliza funções de validação para verificar se o CPF e o horário são válidos.
Retorno: validate_cpf_bd(slot_value, dispatcher) e validate_time_def(slot_value, dispatcher)
9. ValidateCPFActionEvent (FormValidationAction)
Nome da Ação: validate_event_form
Descrição: Valida o CPF e o horário fornecido pelo usuário para marcar uma consulta. A ação utiliza funções de validação para garantir que os dados fornecidos sejam válidos antes de prosseguir com o agendamento.
Retorno: validate_cpf_bd(slot_value, dispatcher) e validate_time_def(slot_value, dispatcher)
10. ValidateAndAddEvent
Nome da Ação: action_add_event
Descrição: Esta ação adiciona uma nova consulta ao banco de dados, gerando um código de evento aleatório e calculando o horário de término com base no horário inicial fornecido pelo usuário. Se o agendamento for bem-sucedido, uma mensagem de confirmação é enviada ao usuário.
Retorno: Em caso de sucesso, SlotSet("time", None), SlotSet("event_completed", True), em caso de erro, a ação limpa os slots relevantes.
11. ActionFindFreeSlots
Nome da Ação: action_find_free_slots
Descrição: Busca e retorna os próximos horários livres no calendário. Faz uma requisição para uma API e retorna uma lista dos próximos horários disponíveis, que são então armazenados em um slot chamado free_slots.
Retorno: SlotSet("free_slots", free_slots), ou uma lista vazia em caso de nenhum horário disponível.
12. ModifyGoogleCalendarEvent
Nome da Ação: action_modify_google_calendar_event
Descrição: Modifica a data de um evento existente (consulta) no Google Calendar. A ação busca o evento pelo CPF do usuário, valida a nova data fornecida e tenta atualizar o evento no calendário.
Retorno: Se bem-sucedido, confirma a alteração ao usuário. Caso contrário, uma mensagem de erro é enviada e os slots relevantes são limpos.
13. ActionDeleteGoogleCalendarEvent
Nome da Ação: action_delete_google_calendar_event
Descrição: Exclui um evento (consulta) do Google Calendar baseado no CPF do usuário. A ação tenta deletar o evento usando uma requisição DELETE e retorna uma mensagem de confirmação ou erro ao usuário.
Retorno: Se bem-sucedido, retorna SlotSet("event_delete_completed", True). Caso contrário, a ação informa o usuário de que a exclusão falhou.