import code
from openai import OpenAI
import backoff 


client = OpenAI(
    api_key="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",
    default_headers={"OpenAI-Beta": "assistants=v2"}
)


def chat_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def generate_from_GPT(prompts, max_tokens, model="gpt-4-1106-preview", temperature=0.7, n=3):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=prompts,
            temperature=temperature,
            max_tokens=max_tokens,
            n=n
        )

        generated_ans = response.choices
        return [choice.message.content.strip() for choice in generated_ans]
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



def Judge_if_got_Answer_from_GPT(prompts, max_tokens, model="gpt-4-1106-preview", temperature=0.7, n=1):
    """
    Generate answer from GPT model with the given prompt.
    input:
        @max_tokens: the maximum number of tokens to generate; in this project, it is 8000 - len(fortran_code)
        @n: the number of samples to return
    return: a list of #n generated_ans when no error occurs, otherwise None

    return example (n=3):
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=prompts,
            max_tokens = max_tokens,
            temperature = temperature,
            n = n
        )
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    
def Find_Answer_from_GPT(prompts, max_tokens, model="gpt-4-1106-preview", temperature=0.7, n=1):
    """
    Generate answer from GPT model with the given prompt.
    input:
        @max_tokens: the maximum number of tokens to generate; in this project, it is 8000 - len(fortran_code)
        @n: the number of samples to return
    return: a list of #n generated_ans when no error occurs, otherwise None

    return example (n=3):
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=prompts,
            max_tokens = max_tokens,
            temperature = temperature,
            n = n
        )
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None