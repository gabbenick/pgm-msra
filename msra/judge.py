from openai import OpenAI
from utils.gpt_robots import create_and_run_assistant
# Certifique-se de que JUDGE_INSTRUCTIONS_CARREIRA está definida em prompt.prompts
# e que é a versão que espera o contexto consolidado.
from prompt.prompts import JUDGE_INSTRUCTIONS_CARREIRA

def explain_career_progression_results(
    client: OpenAI,
    original_user_query: str, # A consulta original para dar contexto ao LLM
    contexto_adicional_calculado: str, # <<< MUDANÇA AQUI no nome do parâmetro
    gpt_config: dict = None
) -> str:
    """
    Chama o assistente Juiz para analisar a progressão, salário (ou erros)
    e fornecer uma explicação final amigável ao usuário.
    """
    if gpt_config is None:
        gpt_config = {}

    # O prompt para o Juiz agora usa o contexto_adicional_calculado
    thread_prompts = [
        {
            "role": "user",
            "content": (
                f"Consulta original do usuário para seu conhecimento e para que você possa contextualizar sua resposta:\n"
                f"'''{original_user_query}'''\n\n"
                f"Abaixo estão as informações consolidadas sobre a progressão de carreira e o possível salário do servidor. "
                f"Sua tarefa é analisar tudo isso e gerar uma explicação final clara, concisa e amigável para o usuário em português brasileiro, "
                f"seguindo as instruções detalhadas do seu perfil (JUDGE_INSTRUCTIONS_CARREIRA).\n\n"
                f"--- INÍCIO DAS INFORMAÇÕES CONSOLIDADAS PARA ANÁLISE ---\n"
                f"{contexto_adicional_calculado}\n" # <<< USA O NOVO PARÂMETRO AQUI
                f"--- FIM DAS INFORMAÇÕES CONSOLIDADAS PARA ANÁLISE ---"
            )
        }
    ]
    
    explanation_text = create_and_run_assistant(
        client=client,
        assistant_name="JuizCarreira", 
        assistant_instructions=JUDGE_INSTRUCTIONS_CARREIRA, # Esta instrução deve estar atualizada
        thread_prompts=thread_prompts,
        **gpt_config 
    )
    return explanation_text