from openai import OpenAI # Para type hinting, se você usa
from utils.gpt_robots import create_and_run_assistant # Certifique-se que este é o caminho correto
from prompt.prompts import JUDGE_INSTRUCTIONS_CARREIRA # Importa a instrução correta

# A gpt_config pode ser útil para passar o modelo, temperatura, etc.
def explain_career_progression_results(
    client: OpenAI, # Adicionando o client como argumento
    progression_timeline_json_str: str,
    original_user_query: str,
    gpt_config: dict = None # Opcional, para configurações como modelo, temperatura
) -> str:
    """
    Chama o assistente Juiz (configurado com JUDGE_INSTRUCTIONS_CARREIRA)
    para revisar a linha do tempo da progressão (ou erro do Executor) e
    explicá-la de forma clara para o usuário em português.

    Args:
        client: Instância do cliente OpenAI.
        progression_timeline_json_str: A string JSON retornada pelo Executor,
                                       contendo a linha do tempo da progressão ou um erro.
        original_user_query: A consulta original do usuário para dar contexto ao Juiz.
        gpt_config: Dicionário opcional com configurações para a chamada do LLM.

    Returns:
        Uma string contendo a explicação formatada para o usuário.
    """
    if gpt_config is None:
        gpt_config = {}

    # O prompt para o Juiz deve incluir a saída do Executor e a consulta original.
    thread_prompts = [
        {
            "role": "user",
            "content": (
                f"A linha do tempo de progressão de carreira (ou mensagem de erro) retornada pelo Executor é:\n"
                f"```json\n{progression_timeline_json_str}\n```\n\n"
                f"Sua tarefa é revisar esta informação e explicar o resultado de forma clara, "
                f"concisa e amigável para o usuário em português brasileiro.\n"
                f"Se o JSON indicar um erro no cálculo ou um problema do Executor, explique isso ao usuário de forma compreensível.\n"
                f"A consulta original do usuário foi: '{original_user_query}'.\n"
                f"Responda APENAS com o texto da explicação final."
            )
        }
    ]

    # Certifique-se que `create_and_run_assistant` aceita `client` como primeiro argumento
    # e que `gpt_config` é desempacotado corretamente como **kwargs.
    explanation_text = create_and_run_assistant(
        client=client,
        assistant_name="JuizCarreira", # Nome descritivo para o assistente
        assistant_instructions=JUDGE_INSTRUCTIONS_CARREIRA,
        thread_prompts=thread_prompts,
        **gpt_config  # Passa configurações como model, temperature, etc.
    )

    return explanation_text

# As funções Judge_condition, Judge_statement, Judge_answer
# do seu judge.py original não são necessárias para este fluxo simplificado
# de progressão de carreira. Você pode comentá-las ou removê-las.