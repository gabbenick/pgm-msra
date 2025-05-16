import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv # Para carregar variáveis de ambiente (API Key)
from openai import OpenAI

# Importe as funções refatoradas dos seus módulos MACM
from macm.thinker import extract_career_progression_data
from macm.executor import calculate_career_progression # Ou o nome com typo se você manteve
from macm.judge import explain_career_progression_results

# Função auxiliar para limpar strings JSON (pode ir para utils se preferir)
def clean_json_string(text_with_json: str) -> str:
    """
    Tenta extrair uma string JSON de um texto que pode conter JSON encapsulado
    em markdown ou com texto antes/depois.
    """
    text_with_json = text_with_json.strip()

    # Tenta encontrar JSON dentro de ```json ... ```
    match_markdown = re.search(r"```json\s*(\{.*?\})\s*```", text_with_json, re.DOTALL)
    if match_markdown:
        return match_markdown.group(1).strip()

    # Tenta encontrar JSON dentro de ``` ... ```
    match_generic_markdown = re.search(r"```\s*(\{.*?\})\s*```", text_with_json, re.DOTALL)
    if match_generic_markdown:
        return match_generic_markdown.group(1).strip()
        
    # Tenta encontrar o primeiro '{' até o último '}' que possa formar um JSON
    # Isso é mais arriscado, mas pode funcionar se o LLM apenas adicionar texto antes/depois
    # e não outros '{' ou '}' desbalanceados.
    try:
        first_brace = text_with_json.find('{')
        last_brace = text_with_json.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            potential_json = text_with_json[first_brace : last_brace+1]
            # Tenta validar se é realmente um JSON
            json.loads(potential_json) # Se não levantar exceção, é provável que seja JSON
            return potential_json.strip()
    except json.JSONDecodeError:
        pass # Não era um JSON válido, continua

    # Se nada funcionou, retorna a string original (ou uma string vazia/erro)
    # Retornar a string original pode levar ao mesmo erro de parseamento,
    # mas dá a chance de a lógica de erro no main.py lidar com isso.
    return text_with_json # Ou talvez: raise ValueError("Não foi possível extrair JSON da string.")


def run_career_progression_pipeline(user_query_pt: str):
    """
    Orquestra o pipeline completo para processar uma consulta de progressão de carreira.
    """
    load_dotenv() # Carrega variáveis do arquivo .env
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Erro: A variável de ambiente OPENAI_API_KEY não foi definida.")
        print("Por favor, crie um arquivo .env na raiz do projeto com sua chave: OPENAI_API_KEY='sk-...'")
        return "Erro de configuração: Chave da API não encontrada."

    try:
        client = OpenAI(api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"})
        client.models.list() # Teste rápido para verificar se a chave e conexão são válidas
        print("Cliente OpenAI inicializado com sucesso.")
    except Exception as e:
        print(f"Falha ao inicializar o cliente OpenAI: {e}")
        return f"Erro de inicialização do cliente OpenAI: {e}"

    # Data atual para referência, caso o usuário diga "até hoje"
    formato_data_padrao = "%d/%m/%Y"
    data_atual_str = datetime.now().strftime(formato_data_padrao)
    
    final_explanation = "Desculpe, ocorreu um problema e não foi possível processar sua solicitação no momento."

    print(f"\n--- Consulta do Usuário (PT) ---\n{user_query_pt}\n")

    # --- Fase 1: Pensador (Thinker) ---
    print("--- Fase 1: Pensador ---")
    # Configurações para o LLM do Pensador (opcional, pode usar defaults de create_and_run_assistant)
    gpt_config_thinker = {"model": "gpt-3.5-turbo-1106"} # Modelo mais rápido e barato para extração
    
    extracted_data_json_str = extract_career_progression_data(
        client=client,
        user_query_content=user_query_pt,
        data_atual_str=data_atual_str,
        gpt_config=gpt_config_thinker
    )
    print(f"Pensador retornou (string bruta):\n{extracted_data_json_str}\n")
    
    extracted_data_json_str = clean_json_string(extracted_data_json_str)
    print(f"Pensador retornou (após limpeza):\n{extracted_data_json_str}\n")
    extracted_data = None
    try:
        extracted_data = json.loads(extracted_data_json_str)
        if "erro" in extracted_data and extracted_data["erro"]:
            error_message = f"Erro na análise da sua solicitação: {extracted_data['erro']}. Por favor, tente reformular sua pergunta."
            print(error_message)
            # Poderia chamar o Juiz para formatar este erro também, se desejado
            return error_message # Retorna o erro diretamente
    except json.JSONDecodeError as e:
        error_message = f"Houve um problema técnico ao processar sua solicitação (formato inválido da análise inicial). Detalhe: {e}. String recebida: '{extracted_data_json_str}'"
        print(error_message)
        return error_message
    except Exception as e: # Outros erros inesperados
        error_message = f"Ocorreu um erro técnico inesperado após a fase de análise inicial. Detalhe: {e}"
        print(error_message)
        return error_message

    if not extracted_data: # Se extracted_data for None devido a um erro não capturado acima
        return "Falha na extração de dados pelo Pensador."

    # --- Fase 2: Executor ---
    print("--- Fase 2: Executor ---")
    # Configurações para o LLM do Executor (modelo mais capaz é crucial aqui)
    gpt_config_executor = {"model": "gpt-4-turbo-preview"} # Fortemente recomendado
    
    progression_timeline_json_str = calculate_career_progression(
        client=client,
        extracted_server_data=extracted_data, # Passa o dict Python parseado
        gpt_config=gpt_config_executor
    )
    print(f"Executor retornou (string bruta):\n{progression_timeline_json_str}\n")

    progression_timeline_json_str = clean_json_string(progression_timeline_json_str)
    print(f"Executor retornou (após limpeza):\n{progression_timeline_json_str}\n")
    # O Juiz receberá esta string e tentará interpretá-la (seja JSON válido ou texto de erro)

    # --- Fase 3: Juiz (Judge) ---
    print("--- Fase 3: Juiz ---")
    gpt_config_judge = {"model": "gpt-4-turbo-preview"} # Pode ser gpt-3.5 para economizar, mas gpt-4 pode dar explicações melhores
    
    final_explanation = explain_career_progression_results(
        client=client,
        progression_timeline_json_str=progression_timeline_json_str,
        original_user_query=user_query_pt,
        gpt_config=gpt_config_judge
    )
    print("--- Explicação Final do Juiz (PT) ---")
    print(final_explanation)
    
    return final_explanation


if __name__ == "__main__":
    # Exemplo de prompt do usuário para progressão de carreira
    # (Baseado na imagem que você compartilhou anteriormente, mas usando a lógica de regras que definimos)
    user_prompt_carreira = """
    Fui admitido em 20 de agosto de 2008, com a referência inicial NE41A01.
    Ao longo da minha carreira, obtive os seguintes títulos e requeri as progressões nas datas indicadas:
    - Título de Nível Médio: requerido em 25 de outubro de 2013.
    - Título de Nível Superior: requerido em 04 de janeiro de 2017.
    - Título de Especialização: requerido em 22 de setembro de 2022.
    Gostaria de ver minha progressão completa até 31 de dezembro de 2023.
    """
    run_career_progression_pipeline(user_prompt_carreira)

    print("\n" + "="*70 + "\n")

    # Exemplo mais simples para teste rápido
    user_prompt_simples = "Minha admissao foi em 01/01/2022 como NE20A01. Quero saber minha progressao ate hoje."
    # run_career_progression_pipeline(user_prompt_simples)