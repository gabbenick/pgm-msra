import time
from openai import OpenAI

def create_and_run_assistant(
    client: OpenAI, 
    assistant_name: str,
    assistant_instructions: str,
    thread_prompts: list,
    model: str = "gpt-4-1106-preview",
    timeout_seconds: int = 180,
    poll_interval_seconds: int = 2
) -> str:
    """
    Cria um assistente, cria uma thread, envia mensagens, executa o run,
    aguarda a conclusão, recupera a resposta e limpa os recursos.

    Args:
        client: Instância do cliente OpenAI.
        assistant_name: Nome para o assistente (para logging/debug).
        assistant_instructions: As instruções específicas para o assistente.
        thread_prompts: Uma lista de prompts a serem adicionados à thread.
        model: O modelo a ser usado para o assistente.
        timeout_seconds: Tempo máximo para aguardar a conclusão do run.
        poll_interval_seconds: Intervalo para checar o status do run.

    Returns:
        A string de texto da última mensagem do assistente, ou uma mensagem de erro.
    """
    assistant = None
    thread = None
    run_id = None
    start_time = time.time()

    try:
        assistant = client.beta.assistants.create(
            model=model,
            instructions=assistant_instructions,
            name=assistant_name,
            tools=[{"type": "code_interpreter"}],
        )

        thread = client.beta.threads.create()

        for prompt_item in thread_prompts: # Renomeado para prompt_item
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role=prompt_item.get("role", "user"),
                content=prompt_item.get("content", ""),
            )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )
        run_id = run.id

        while run.status in ["queued", "in_progress", "requires_action"]:
            if time.time() - start_time > timeout_seconds:
                try:
                    client.beta.threads.runs.cancel(thread_id=thread.id, run_id=run.id)
                except Exception as cancel_err:
                    print(f"Erro ao tentar cancelar run {run.id} por timeout: {cancel_err}")
                return f"Erro: Timeout ({timeout_seconds}s) para o assistente '{assistant_name}' (Run ID: {run_id})."

            time.sleep(poll_interval_seconds)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls if run.required_action and run.required_action.type == "submit_tool_outputs" else None
                print(f"Run {run.id} para '{assistant_name}' requer ação. Tipo: {run.required_action.type if run.required_action else 'N/A'}. Tool calls: {tool_calls}")

        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id, order="desc")
            for message in messages.data:
                if message.run_id == run.id and message.role == "assistant":
                    if message.content and len(message.content) > 0:
                        content_block = message.content[0]
                        if content_block.type == 'text':
                            return content_block.text.value
                        else:
                            return f"Erro: Assistente '{assistant_name}' retornou conteúdo não textual ({content_block.type})."
                    else:
                        return f"Erro: Assistente '{assistant_name}' enviou uma mensagem vazia."
            return f"Erro: Nenhuma mensagem do assistente '{assistant_name}' encontrada para o run {run.id}."
        else:
            error_detail = f" Detalhe: {run.last_error.code} - {run.last_error.message}" if run.last_error else ""
            return f"Erro: Run {run.id} para '{assistant_name}' finalizou com status '{run.status}'.{error_detail}"

    except Exception as e:
        print(f"Exceção crítica ao executar o assistente '{assistant_name}' (Run ID: {run_id}): {type(e).__name__} - {e}")
        return f"Exceção crítica ao executar assistente '{assistant_name}': {str(e)}"
    finally:
        if assistant:
            try:
                client.beta.assistants.delete(assistant.id)
            except Exception as e_del_ass:
                print(f"Erro ao deletar assistente {assistant.id} ('{assistant_name}'): {e_del_ass}")
        if thread:
            try:
                client.beta.threads.delete(thread.id)
            except Exception as e_del_thr:
                print(f"Erro ao deletar thread {thread.id} para '{assistant_name}': {e_del_thr}")

