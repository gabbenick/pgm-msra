import time
from openai import OpenAI

client = OpenAI(
    api_key="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",
    default_headers={"OpenAI-Beta": "assistants=v2"}
)

def create_and_run_assistant(role, prompts, model="gpt-4-1106-preview", **kwargs):

    role_instructions = {
        "Thinker": """You are a thinker. I need you to help me think about some problems.
        You need to provide me the answer based on the format of the example.""",
        "Judge": """You're a judge. I need you to make judgments on some statements.""",
        "Executor": """You're an executor. I need you to calculate the final result based on some conditions and steps.
        You need to provide me the answer based on the format of the examples."""
    }

    assistant = client.beta.assistants.create(
    model=model,
    instructions=role_instructions.get(role, ""),
    name=role,
    tools=[{"type": "code_interpreter"}],
    )


    thread = client.beta.threads.create()

    for prompt in prompts:
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt["content"],
        )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    if run.status == "completed":
        all_messages = client.beta.threads.messages.list(thread_id=thread.id)
        try:
            for message in all_messages.data:
                if message.role == "assistant":
                    response = message.content[0].text.value
                    break
            else:
                response = "No assistant message found."
        except Exception as e:
            print(f"An error occurred while parsing assistant response: {e}")
            response = "I need to rethink this problem."
    else:
        print(f"Run status: {run.status}")
        response = f"Run failed with status: {run.status}"
    print(run)
    return response


def generate_from_thinker(prompts, **kwargs):
    return create_and_run_assistant("Thinker", prompts, **kwargs)

def generate_from_judge(prompts, **kwargs):
    return create_and_run_assistant("Judge", prompts, **kwargs)

def generate_from_excutor(prompts, **kwargs):
    return create_and_run_assistant("Executor", prompts, **kwargs)
