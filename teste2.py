import openai

client = openai.OpenAI(api_key="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")

res = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello, can you return the value of 2+2?"}]
)

print(res.choices[0].message.content)
