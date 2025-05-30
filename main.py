# main.py
import os
import json
import re # Para a função clean_json_string, se usar regex mais avançado
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Importe suas funções MACM (ou msra, como no seu exemplo)
from msra.thinker import extract_career_progression_data
from msra.executor import calculate_career_progression
from msra.judge import explain_career_progression_results

# --- CONFIGURAÇÃO DA TABELA SALARIAL ---
# Esta estrutura deve ser carregada de um arquivo JSON/CSV em um sistema real.
# As CHAVES dos cargos aqui devem ser normalizadas (ex: tudo minúsculo)
# para facilitar o matching com o que o Pensador extrair.
TABELAS_SALARIAIS_POR_CARGO = {
    "administracao_geral": { # Chave normalizada para o cargo principal
        "NE01": { 
            "A01": 1015.11, "A02": 1065.84, "A03": 1116.10, "A04": 1171.91, "A05": 1230.43, "A06": 1292.03,
            "B01": 1356.59, "B02": 1424.44, "B03": 1495.66, "B04": 1570.42, "B05": 1649.02, "B06": 1731.42,
            "C01": 1817.98, "C02": 1908.89, "C03": 2004.31, "C04": 2104.60, "C05": 2209.77, "C06": 2320.28,
            "D01": 2436.30, "D02": 2558.11, "D03": 2686.05, "D04": 2820.32, "D05": 2961.28, "D06": 3109.37
        },
        "NE02": { 
            "A01": 1600.00, "A02": 1670.00, # Adicione mais níveis e classes se necessário
            "D06": 3300.00
        },
        "NS01": { 
            "A01": 2800.00, "A02": 2900.00, # Adicione mais níveis e classes se necessário
            "D06": 5500.00
        },
        # Adicione as outras 3 variações de prefixo para "administracao_geral" aqui (NM01, NM02, NS02)
        # Exemplo:
        # "NM01": { "A01": YYYY.YY, ... "D06": ZZZZ.ZZ },
    },
    # Adicione aqui as entradas para os outros 5 tipos de cargo canônicos
    # Exemplo:
    # "professor_magisterio_superior": {
    #     "MG40DE": { "I01": ..., "TITULAR01": ... }
    # },

    "cargo_desconhecido": { # <<< CHAVE DE FALLBACK NO NÍVEL SUPERIOR
        "XX00": { # Um prefixo genérico de fallback DENTRO de cargo_desconhecido
            "A01": 1000.00, 
            "D06": 1500.00  
        }
        # Você também poderia ter prefixos mais comuns aqui como fallback,
        # por exemplo, se NE01 for um default muito comum:
        # "NE01": {
        #     "A01": 1015.11, ... # Uma cópia da tabela NE01 de admin geral, por exemplo
        # }
    }
}
TABELAS_SALARIAIS_CARREGADAS = TABELAS_SALARIAIS_POR_CARGO


def clean_json_string(text_with_json: str) -> str:
    """Tenta extrair uma string JSON de um texto que pode conter JSON."""
    text_with_json = text_with_json.strip()
    # Tenta encontrar JSON dentro de ```json ... ``` ou ``` ... ```
    match_markdown = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text_with_json, re.DOTALL)
    if match_markdown:
        potential_json = match_markdown.group(1).strip()
        try:
            json.loads(potential_json) # Valida se o conteúdo é JSON
            return potential_json
        except json.JSONDecodeError:
            # Se não for JSON válido dentro do markdown, tenta o próximo método
            pass

    # Tenta encontrar o primeiro '{' até o último '}' ou '[' até ']'
    # que possa formar um JSON válido.
    match_direct_json = re.search(r"(\{[\s\S]*\})|(\[[\s\S]*\])", text_with_json, re.DOTALL)
    if match_direct_json:
        potential_json = match_direct_json.group(0).strip()
        try:
            json.loads(potential_json) # Valida
            return potential_json
        except json.JSONDecodeError:
            pass
            
    return text_with_json # Retorna original se nenhuma extração/validação for bem-sucedida


def get_salario_final(
    tipo_cargo_extraido: str | None,
    ultima_referencia_completa: str, # ex: "NE01A01", "NS40D06"
    tabelas_salariais_por_cargo: dict
) -> tuple[float | None, str]:
    """
    Busca o salário na estrutura de tabelas aninhadas.
    """
    if not tabelas_salariais_por_cargo:
        return None, "Configuração de erro: Tabela salarial principal não carregada."

    if not ultima_referencia_completa or len(ultima_referencia_completa) < 5: # Minimo como X0A01
        return None, f"Referência final '{ultima_referencia_completa}' é inválida para busca salarial."

    # 1. Determinar qual tabela de CARGO PRINCIPAL usar
    cargo_chave_para_tabela = "cargo_desconhecido" # Fallback se o Pensador retornar isso ou None
    cargo_nome_display = "Cargo (Não Especificado/Desconhecido)"

    if tipo_cargo_extraido and isinstance(tipo_cargo_extraido, str) and tipo_cargo_extraido.strip():
        # Assume que tipo_cargo_extraido é uma das chaves canônicas (ex: "administracao_geral")
        if tipo_cargo_extraido in tabelas_salariais_por_cargo:
            cargo_chave_para_tabela = tipo_cargo_extraido
            cargo_nome_display = tipo_cargo_extraido.replace("_", " ").title()
        else:
            # Se o Pensador retornou algo não listado como chave principal, usa fallback
            # mas mantém o nome que o Pensador retornou para display
            cargo_nome_display = f"{tipo_cargo_extraido} (não mapeado, usando tabela genérica)"
            # cargo_chave_para_tabela já é "cargo_desconhecido"
    
    tabela_do_cargo_principal = tabelas_salariais_por_cargo.get(cargo_chave_para_tabela)

    if not tabela_do_cargo_principal:
        return None, f"Falha crítica: Tabela para '{cargo_nome_display}' (ou fallback '{cargo_chave_para_tabela}') não existe na configuração."

    # 2. Separar Prefixo (Grupo+Carga) e Sufixo (ClasseNivel) da referência
    # Este regex precisa ser robusto para todos os seus formatos.
    # (Grupo1: Prefixo LetrasNumeros, Grupo2: Classe Letras, Grupo3: Nivel Numeros)
    match_ref_parts = re.match(r"([A-Z0-9]+)([A-Z]+)(\d+)", ultima_referencia_completa)
    if not match_ref_parts:
        return None, f"Formato da referência final '{ultima_referencia_completa}' não reconhecido. Esperado: Prefixo(ex:NE01)Classe(ex:A)Nivel(ex:01)."

    prefixo_referencia = match_ref_parts.group(1)    # Ex: "NE01", "MG40DE"
    classe_referencia = match_ref_parts.group(2)     # Ex: "A", "I", "TITULAR"
    nivel_referencia_str = match_ref_parts.group(3) # Ex: "01", "06"
    sufixo_classe_nivel = f"{classe_referencia}{nivel_referencia_str}" # Recompõe para chave da sub-tabela: "A01"

    # 3. Buscar a SUB-TABELA pelo PREFIXO DA REFERÊNCIA
    sub_tabela_salarial_especifica = tabela_do_cargo_principal.get(prefixo_referencia)

    if not sub_tabela_salarial_especifica:
        # Se o prefixo não existe no cargo encontrado, tenta o prefixo no cargo_desconhecido
        print(f"AVISO: Prefixo '{prefixo_referencia}' não encontrado para '{cargo_nome_display}'. Tentando fallback geral para o prefixo.")
        tabela_fallback_geral = tabelas_salariais_por_cargo.get("cargo_desconhecido", {})
        sub_tabela_salarial_especifica = tabela_fallback_geral.get(prefixo_referencia)
        
        if sub_tabela_salarial_especifica:
            cargo_nome_display += " (usando tabela de prefixo de fallback)"
        else:
            # Se nem no fallback geral o prefixo existe, tenta o primeiro prefixo do fallback geral
            if tabela_fallback_geral:
                chaves_prefixo_fallback = list(tabela_fallback_geral.keys())
                if chaves_prefixo_fallback:
                    primeiro_prefixo_fallback = chaves_prefixo_fallback[0]
                    sub_tabela_salarial_especifica = tabela_fallback_geral.get(primeiro_prefixo_fallback)
                    if sub_tabela_salarial_especifica:
                        print(f"AVISO: Usando prefixo de fallback MUITO genérico '{primeiro_prefixo_fallback}' para referência original '{ultima_referencia_completa}'.")
                        cargo_nome_display += f" (usando tabela de prefixo fallback '{primeiro_prefixo_fallback}')"

        if not sub_tabela_salarial_especifica:
             return None, f"Não foi encontrada sub-tabela salarial para o prefixo '{prefixo_referencia}' no cargo '{cargo_nome_display}' ou em qualquer fallback."

    # 4. Buscar o SALÁRIO na sub-tabela usando o SUFIXO (ClasseNivel)
    salario = sub_tabela_salarial_especifica.get(sufixo_classe_nivel)

    if salario is not None:
        return salario, f"Para o cargo '{cargo_nome_display}' e referência {ultima_referencia_completa}, o salário base é R$ {salario:.2f}."
    else:
        return None, f"A Classe/Nível '{sufixo_classe_nivel}' não foi encontrada na tabela salarial para o prefixo '{prefixo_referencia}' do cargo '{cargo_nome_display}'."

def run_career_progression_pipeline(user_query_pt: str):
    """
    Orquestra o pipeline completo para processar uma consulta de progressão de carreira.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Erro: A variável de ambiente OPENAI_API_KEY não foi definida.")
        return "Erro de configuração: Chave da API não encontrada."
    try:
        client = OpenAI(api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"})
        client.models.list()
        print("Cliente OpenAI inicializado com sucesso.")
    except Exception as e:
        print(f"Falha ao inicializar o cliente OpenAI: {e}")
        return f"Erro de inicialização do cliente OpenAI: {e}"

    formato_data_padrao = "%d/%m/%Y"
    data_atual_str = datetime.now().strftime(formato_data_padrao)
    
    print(f"\n--- Consulta do Usuário (PT) ---\n{user_query_pt}\n")

    # --- Fase 1: Pensador ---
    print("--- Fase 1: Pensador ---")
    gpt_config_thinker = {"model": "gpt-3.5-turbo-1106"}
    extracted_data_json_str = extract_career_progression_data(
        client, user_query_pt, data_atual_str, gpt_config=gpt_config_thinker
    )
    print(f"Pensador retornou (string bruta):\n{extracted_data_json_str}\n")
    extracted_data_json_str_limpa = clean_json_string(extracted_data_json_str)
    print(f"Pensador retornou (após limpeza):\n{extracted_data_json_str_limpa}\n")
    
    extracted_data = None
    try:
        extracted_data = json.loads(extracted_data_json_str_limpa)
        if "erro" in extracted_data and extracted_data["erro"]:
            error_message = f"Erro na análise da sua solicitação pelo Pensador: {extracted_data['erro']}. Por favor, tente reformular sua pergunta."
            print(error_message)
            return error_message
    except json.JSONDecodeError as e:
        error_message = f"Houve um problema técnico (Pensador não retornou JSON válido). Detalhe: {e}. String recebida: '{extracted_data_json_str}'"
        print(error_message)
        return error_message
    except Exception as e:
        error_message = f"Ocorreu um erro técnico inesperado após o Pensador. Detalhe: {e}"
        print(error_message)
        return error_message

    if not extracted_data:
        return "Falha crítica na extração de dados pelo Pensador."

    # --- Fase 2: Executor ---
    print("--- Fase 2: Executor ---")
    gpt_config_executor = {"model": "gpt-4-0125-preview", "temperature": 0.0} # ou gpt-4-turbo-preview
    progression_timeline_json_str_bruta = calculate_career_progression(
        client, extracted_data, gpt_config=gpt_config_executor
    )
    print(f"Executor retornou (string bruta):\n{progression_timeline_json_str_bruta}\n")
    progression_timeline_json_str_limpa = clean_json_string(progression_timeline_json_str_bruta)
    print(f"Executor retornou (após limpeza):\n{progression_timeline_json_str_limpa}\n")

    # --- INTERMEDIÁRIO: Processamento Python da Saída do Executor e Cálculo Salarial ---
    tipo_cargo_servidor = extracted_data.get("tipo_cargo") # Pego do Pensador
    contexto_para_juiz = "" # Mensagem consolidada para o Juiz

    try:
        lista_progressoes = json.loads(progression_timeline_json_str_limpa)

        if isinstance(lista_progressoes, list) and lista_progressoes:
            ultimo_evento = lista_progressoes[-1]
            ultima_referencia_servidor = ultimo_evento.get("referencia")
            
            contexto_para_juiz = f"A progressão de carreira calculada para o servidor é:\n{json.dumps(lista_progressoes, indent=2, ensure_ascii=False)}\n\n"

            if ultima_referencia_servidor:
                salario_calculado, msg_status_salario = get_salario_final(
                    tipo_cargo_servidor,
                    ultima_referencia_servidor,
                    TABELAS_SALARIAIS_CARREGADAS # Usa a tabela carregada/definida
                )
                contexto_para_juiz += msg_status_salario
                print(f"INFO SALÁRIO (Python): {msg_status_salario}")
            else:
                contexto_para_juiz += "Não foi possível determinar a última referência da progressão para o cálculo salarial."
        
        elif isinstance(lista_progressoes, dict) and "erro_calculo" in lista_progressoes:
            contexto_para_juiz = f"Ocorreu um erro durante o cálculo da progressão pelo Executor: {lista_progressoes['erro_calculo']}"
        else:
            contexto_para_juiz = f"O Executor retornou um formato de progressão inesperado: '{progression_timeline_json_str_limpa}'"

    except json.JSONDecodeError:
        contexto_para_juiz = f"Erro: Executor não retornou um JSON válido para a progressão. Saída do Executor: '{progression_timeline_json_str_bruta}'"
    except Exception as e:
        contexto_para_juiz = f"Erro inesperado ao processar a saída do Executor ou calcular o salário: {str(e)}"
    
    print(f"\nContexto consolidado para o Juiz:\n{contexto_para_juiz}\n")

    # --- Fase 3: Juiz ---
    print("--- Fase 3: Juiz ---")
    gpt_config_judge = {"model": "gpt-4-turbo-preview"}
    
    final_explanation = explain_career_progression_results(
        client=client,
        original_user_query=user_query_pt,
        contexto_adicional_calculado=contexto_para_juiz, # Passa a string consolidada
        gpt_config=gpt_config_judge
    )
    
    print("--- Explicação Final do Juiz (PT) ---")
    print(final_explanation)
    return final_explanation

if __name__ == "__main__":
    user_prompt_carreira = """
Por favor, simule a progressão de carreira para um servidor da Administração Geral com os seguintes dados:

- Data de Admissão: 01/03/2005
- Referência Inicial: NE01A01
- Data Limite para Simulação: 31/12/2035

Histórico de Títulos (com datas de requerimento da progressão):
1.  Título de Nível Médio: Requerido em 15/07/2011.
2.  Título de Nível Superior (Graduação): Requerido em 01/09/2014.
3.  Título de Especialização (Pós-Graduação Lato Sensu): Requerido em 20/10/2019.
4.  Título de Mestrado: Requerido em 05/12/2027.

Gostaria de ver a linha do tempo completa da progressão e o salário correspondente à última referência alcançada.
"""
    run_career_progression_pipeline(user_prompt_carreira)

    print("\n" + "="*70 + "\n")
