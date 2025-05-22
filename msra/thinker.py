from openai import OpenAI
from utils.gpt_robots import create_and_run_assistant
from prompt.prompts import THINKER_INSTRUCTIONS_CARREIRA

def extract_career_progression_data(
    client: OpenAI, 
    user_query_content: str,
    data_atual_str: str,
    gpt_config: dict = None
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

    thread_prompts = [
        {
            "role": "user",
            "content": (
                f"Analise esta consulta do usuário sobre progressão de carreira: '{user_query_content}'. "
                f"Data atual para referência (se 'até hoje' for mencionado pelo usuário): {data_atual_str}."
            )
        }
    ]

    
    json_response_str = create_and_run_assistant(
        client=client,
        assistant_name="PensadorCarreira",
        assistant_instructions=THINKER_INSTRUCTIONS_CARREIRA,
        thread_prompts=thread_prompts,
        **gpt_config
    )

    return json_response_str
