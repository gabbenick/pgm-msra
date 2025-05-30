import json # Para o json.dumps, caso necessário internamente, mas principalmente para o main.py
from openai import OpenAI
from utils.gpt_robots import create_and_run_assistant
from prompt.prompts import EXECUTOR_INSTRUCTIONS_CARREIRA, REGULAMENTO_PCC_GERAL_PT # Importa as instruções e o regulamento

# macm/executor.py
# ... (imports) ...
from prompt.prompts import EXECUTOR_INSTRUCTIONS_CARREIRA, REGULAMENTO_PCC_GERAL_PT # Adicione REGULAMENTO aqui se ele não for mais passado como string

def calculate_career_progression(
    client: OpenAI,
    extracted_server_data: dict,
    gpt_config: dict = None 
) -> str:
    if gpt_config is None: 
        gpt_config = {}

    thread_prompts = [
        {
            "role": "user",
            "content": (
                f"REGULAMENTO GERAL DE PROGRESSÃO DE CARREIRA APLICÁVEL:\n"
                f"--- INÍCIO DO REGULAMENTO ---\n{REGULAMENTO_PCC_GERAL_PT}\n--- FIM DO REGULAMENTO ---\n\n"
                f"DADOS DO SERVIDOR (incluindo referência inicial específica do cargo e tipo de cargo):\n"
                f"```json\n{json.dumps(extracted_server_data)}\n```\n\n"
                f"Sua tarefa é, usando o `code_interpreter` e seguindo o REGULAMENTO GERAL, simular a progressão da REFERÊNCIA do servidor a partir da `ref_inicial` fornecida nos dados. "
                f"A parte inicial da `ref_inicial` (os 4 primeiros caracteres) permanecerá constante. "
                f"Concentre-se em progredir a Classe e o Nível (últimos 3 caracteres, com nível de dois dígitos). "
                f"As instruções detalhadas de como proceder estão no seu perfil (EXECUTOR_INSTRUCTIONS_CARREIRA). "
                f"Retorne APENAS a string JSON da linha do tempo da progressão da REFERÊNCIA ou um JSON com \"erro_calculo\" se falhar."
            )
        }
    ]

    # Extrai model e temperature do gpt_config, com defaults apropriados para o Executor
    model_to_use = gpt_config.get("model", "gpt-4-0125-preview") 
    temperature_to_use = gpt_config.get("temperature", 0.0)  # Default 0.0 para Executor
    
    # Garante que a temperatura seja float
    if isinstance(temperature_to_use, str): 
        try: 
            temperature_to_use = float(temperature_to_use)
        except ValueError:
            print(f"AVISO EXECUTOR: Temperatura inválida '{temperature_to_use}', usando default 0.0")
            temperature_to_use = 0.0
    elif not isinstance(temperature_to_use, float) and not isinstance(temperature_to_use, int):
        print(f"AVISO EXECUTOR: Tipo de temperatura inesperado '{type(temperature_to_use)}', usando default 0.0")
        temperature_to_use = 0.0


    progression_json_str = create_and_run_assistant(
        client=client,
        assistant_name="ExecutorCarreira",
        assistant_instructions=EXECUTOR_INSTRUCTIONS_CARREIRA, # Esta deve ser a versão detalhada
        thread_prompts=thread_prompts,
        model=model_to_use,
        temperature=temperature_to_use 
        # Se create_and_run_assistant tiver outros parâmetros como timeout, poll_interval,
        # eles usariam seus defaults ou você os pegaria de gpt_config também.
    )
    return progression_json_str
