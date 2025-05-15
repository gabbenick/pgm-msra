from openai import OpenAI # Para type hinting, se você usa
from utils.gpt_robots import create_and_run_assistant # Certifique-se que este é o caminho correto
from prompt.prompts import THINKER_INSTRUCTIONS_CARREIRA # Importa a instrução correta

# A gpt_config pode ser útil para passar o modelo, temperatura, etc.
# Se você não estiver usando gpt_config para esses parâmetros específicos para o Thinker,
# pode remover e usar os defaults de create_and_run_assistant ou passar explicitamente.
def extract_career_progression_data(
    client: OpenAI, # Adicionando o client como argumento
    user_query_content: str,
    data_atual_str: str,
    gpt_config: dict = None # Opcional, para configurações como modelo, temperatura
) -> str:
    """
    Chama o assistente Pensador (configurado com THINKER_INSTRUCTIONS_CARREIRA)
    para extrair dados estruturados (data_admissao, ref_inicial, titulos, data_limite)
    da consulta do usuário sobre progressão de carreira.

    Args:
        client: Instância do cliente OpenAI.
        user_query_content: A consulta do usuário em texto.
        data_atual_str: A data atual formatada como string ("dd/mm/yyyy") para referência
                        se o usuário mencionar "até hoje".
        gpt_config: Dicionário opcional com configurações para a chamada do LLM (ex: model).

    Returns:
        Uma string JSON contendo os dados extraídos ou uma string JSON de erro.
    """
    if gpt_config is None:
        gpt_config = {}

    # O prompt para o Pensador deve incluir a data atual para o caso de "até hoje"
    # e a consulta original do usuário.
    thread_prompts = [
        {
            "role": "user",
            "content": (
                f"Analise esta consulta do usuário sobre progressão de carreira: '{user_query_content}'. "
                f"Data atual para referência (se 'até hoje' for mencionado pelo usuário): {data_atual_str}."
            )
        }
    ]

    # Certifique-se que `create_and_run_assistant` aceita `client` como primeiro argumento
    # e que `gpt_config` é desempacotado corretamente como **kwargs.
    # Se `gpt_config` contém 'model', ele será usado. Caso contrário, o default de `create_and_run_assistant`.
    json_response_str = create_and_run_assistant(
        client=client,
        assistant_name="PensadorCarreira", # Nome descritivo para o assistente
        assistant_instructions=THINKER_INSTRUCTIONS_CARREIRA,
        thread_prompts=thread_prompts,
        **gpt_config  # Passa configurações como model, temperature, etc.
    )

    return json_response_str

# As funções Analysis_conditions, Fix_conditions, Think_thoughts, Think_Steps
# do seu thinker.py original não são necessárias para este fluxo simplificado
# de progressão de carreira. Você pode comentá-las ou removê-las deste arquivo
# se ele for dedicado apenas ao "Pensador" da progressão de carreira.
# Se você planeja usar este thinker.py para outros problemas que seguem
# aquele framework mais complexo, então você precisaria de uma lógica para
# decidir qual tipo de "pensamento" aplicar. Mas para agora, vamos focar.