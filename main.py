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
   "administracao_geral": {
       # Nível Elementar 30 Horas
       "NE01": {
           "A01": 1015.11, "A02": 1065.84, "A03": 1116.10, "A04": 1171.91, "A05": 1230.43, "A06": 1292.03,
           "B01": 1356.59, "B02": 1424.44, "B03": 1495.66, "B04": 1570.42, "B05": 1649.02, "B06": 1731.42,
           "C01": 1817.98, "C02": 1908.89, "C03": 2004.31, "C04": 2104.60, "C05": 2209.77, "C06": 2320.28,
           "D01": 2436.30, "D02": 2558.11, "D03": 2686.05, "D04": 2820.32, "D05": 2961.28, "D06": 3109.37
       },
       # Nível Médio 30 Horas
       "NM01": {
           "A01": 1316.05, "A02": 1381.87, "A03": 1451.03, "A04": 1523.35, "A05": 1599.71, "A06": 1679.72,
           "B01": 1763.65, "B02": 1851.89, "B03": 1944.47, "B04": 2041.75, "B05": 2143.77, "B06": 2250.97,
           "C01": 2363.49, "C02": 2481.64, "C03": 2605.74, "C04": 2736.08, "C05": 2872.92, "C06": 3016.55,
           "D01": 3167.36, "D02": 3325.70, "D03": 3492.01, "D04": 3666.60, "D05": 3849.89, "D06": 4043.25
       },
       # Nível Superior 30 Horas
       "NS01": {
           "A01": 1728.65, "A02": 1815.01, "A03": 1905.79, "A04": 2001.09, "A05": 2101.16, "A06": 2206.18,
           "B01": 2316.53, "B02": 2432.38, "B03": 2553.95, "B04": 2681.71, "B05": 2815.77, "B06": 2956.48,
           "C01": 3104.28, "C02": 3259.52, "C03": 3422.48, "C04": 3593.67, "C05": 3773.37, "C06": 3962.08,
           "D01": 4160.13, "D02": 4368.13, "D03": 4586.50, "D04": 4815.87, "D05": 5056.63, "D06": 5309.46
       },
       # Nível Elementar 40 Horas
       "NE41": {
           "A01": 1349.82, "A02": 1417.27, "A03": 1488.15, "A04": 1562.53, "A05": 1640.66, "A06": 1722.69,
           "B01": 1808.84, "B02": 1899.30, "B03": 1994.22, "B04": 2093.93, "B05": 2198.67, "B06": 2308.61,
           "C01": 2423.99, "C02": 2545.14, "C03": 2672.42, "C04": 2806.08, "C05": 2946.41, "C06": 3093.72,
           "D01": 3248.37, "D02": 3410.80, "D03": 3581.35, "D04": 3760.44, "D05": 3948.43, "D06": 4145.86
       },
       # Nível Médio 40 Horas
       "NM41": {
           "A01": 1754.81, "A02": 1842.56, "A03": 1934.73, "A04": 2031.42, "A05": 2133.03, "A06": 2239.65,
           "B01": 2351.68, "B02": 2469.17, "B03": 2592.65, "B04": 2775.31, "B05": 2858.37, "B06": 3001.39,
           "C01": 3151.37, "C02": 3309.03, "C03": 3474.43, "C04": 3648.14, "C05": 3830.56, "C06": 4022.07,
           "D01": 4223.11, "D02": 4434.37, "D03": 4656.11, "D04": 4888.86, "D05": 5133.33, "D06": 5390.00
       },
       # Nível Superior 40 Horas
       "NS41": {
           "A01": 2304.85, "A02": 2420.10, "A03": 2541.16, "A04": 2668.18, "A05": 2801.58, "A06": 2941.62,
           "B01": 3088.70, "B02": 3243.17, "B03": 3405.35, "B04": 3575.60, "B05": 3754.42, "B06": 3942.14,
           "C01": 4139.24, "C02": 4346.18, "C03": 4563.49, "C04": 4791.71, "C05": 5031.27, "C06": 5282.80,
           "D01": 5546.93, "D02": 5824.35, "D03": 6115.46, "D04": 6421.26, "D05": 6742.35, "D06": 7079.45
       }
   },
   "auditor_fiscal_tributos": {
       "FIS0": {
           "001": 4327.59,
           "002": 4976.70,
           "003": 5723.21,
           "004": 6581.73
       }
   },
   "agente_controle_arrecadacao": {
       "ACA0": {
           "001": 1130.02,
           "002": 1299.50
       }
   },
   "cargo_desconhecido": {
       "XX00": {
           "A01": 1000.00, 
           "D06": 1500.00  
       },
       "NE01": {
           "A01": 1015.11, "A02": 1065.84, "A03": 1116.10, "A04": 1171.91, "A05": 1230.43, "A06": 1292.03,
           "B01": 1356.59, "B02": 1424.44, "B03": 1495.66, "B04": 1570.42, "B05": 1649.02, "B06": 1731.42,
           "C01": 1817.98, "C02": 1908.89, "C03": 2004.31, "C04": 2104.60, "C05": 2209.77, "C06": 2320.28,
           "D01": 2436.30, "D02": 2558.11, "D03": 2686.05, "D04": 2820.32, "D05": 2961.28, "D06": 3109.37
       }
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
