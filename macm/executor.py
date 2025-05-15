import json # Para o json.dumps, caso necessário internamente, mas principalmente para o main.py
from openai import OpenAI # Para type hinting
from utils.gpt_robots import create_and_run_assistant # Certifique-se que este é o caminho correto
from prompt.prompts import EXECUTOR_INSTRUCTIONS_CARREIRA, REGULAMENTO_PCC_GERAL_PT # Importa as instruções e o regulamento

# Mantendo seu typo na função se você o utiliza consistentemente.
# Caso contrário, corrija para generate_from_executor.
def calculate_career_progression(
    client: OpenAI, # Adicionando o client como argumento
    extracted_server_data: dict, # Espera-se um dict Python aqui (JSON parseado do Pensador)
    gpt_config: dict = None # Opcional, para configurações como modelo, temperatura
) -> str:
    """
    Chama o assistente Executor (configurado com EXECUTOR_INSTRUCTIONS_CARREIRA)
    para calcular/simular a progressão de carreira do servidor.

    O Executor receberá o REGULAMENTO_PCC_GERAL_PT e os dados do servidor,
    e deve usar o code_interpreter para realizar a simulação.

    Args:
        client: Instância do cliente OpenAI.
        extracted_server_data: Um dicionário Python contendo os dados do servidor
                               extraídos pelo Pensador (data_admissao, ref_inicial,
                               titulos_requeridos, data_limite).
        gpt_config: Dicionário opcional com configurações para a chamada do LLM.

    Returns:
        Uma string JSON contendo a lista de eventos da progressão
        ou uma string JSON de erro (ex: {"erro_calculo": "mensagem"}).
    """
    if gpt_config is None:
        gpt_config = {}

    # O prompt para o Executor deve incluir o REGULAMENTO e os dados do servidor.
    # EXECUTOR_INSTRUCTIONS_CARREIRA já detalha como o LLM deve usar esses dois inputs.
    thread_prompts = [
        {
            "role": "user",
            "content": (
                f"Aqui está o REGULAMENTO do PCC que você deve usar para o cálculo:\n"
                f"--- INÍCIO DO REGULAMENTO ---\n{REGULAMENTO_PCC_GERAL_PT}\n--- FIM DO REGULAMENTO ---\n\n"
                f"E aqui estão os DADOS DO SERVIDOR extraídos pelo Pensador (fornecidos como um objeto JSON dentro deste prompt):\n"
                f"```json\n{json.dumps(extracted_server_data)}\n```\n\n"
                f"Sua tarefa é seguir as instruções detalhadas no seu perfil de Executor "
                f"(EXECUTOR_INSTRUCTIONS_CARREIRA) para calcular a progressão de carreira. "
                f"Lembre-se de usar o `code_interpreter` para cálculos de data e para manter o estado da progressão. "
                f"Retorne APENAS a string JSON da linha do tempo ou um JSON com \"erro_calculo\" se falhar."
            )
        }
    ]

    # Recomenda-se um modelo mais capaz para a tarefa complexa do Executor.
    # Se 'model' não estiver em gpt_config, o default de create_and_run_assistant será usado.
    # É melhor definir explicitamente aqui ou no main.py ao chamar.
    final_model_config = {"model": "gpt-4-turbo-preview"} # Sugestão
    if gpt_config and "model" in gpt_config:
        final_model_config["model"] = gpt_config["model"] # Permite override
    # Adiciona outras configs de gpt_config se existirem
    for key, value in gpt_config.items():
        if key != "model":
            final_model_config[key] = value


    # Certifique-se que `create_and_run_assistant` aceita `client` como primeiro argumento
    # e que `final_model_config` é desempacotado corretamente como **kwargs.
    progression_json_str = create_and_run_assistant(
        client=client,
        assistant_name="ExecutorCarreira", # Nome descritivo
        assistant_instructions=EXECUTOR_INSTRUCTIONS_CARREIRA,
        thread_prompts=thread_prompts,
        **final_model_config # Passa configurações como model, temperature, etc.
    )

    return progression_json_str

# As funções Execute_steps e Find_Answer do seu executor.py original
# não são diretamente aplicáveis ao nosso fluxo de progressão de carreira,
# onde o "plano" ou "passos" estão embutidos no REGULAMENTO.
# Você pode comentá-las ou removê-las.