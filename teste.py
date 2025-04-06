from openai import OpenAI

client = OpenAI(
    api_key="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",
    default_headers={"OpenAI-Beta": "assistants=v2"}
)

assistant = client.beta.assistants.create(
    name="Teste",
    instructions="Você é um assistente de teste",
    tools=[],
    model="gpt-4-1106-preview"
)

print("Assistant criado com sucesso:")
print(assistant.id)
