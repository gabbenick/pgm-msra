import os
import re
import json
import random
from prompt.prompts import *
from collections import Counter
from macm.executor import Execute_steps
from macm.judge import Judge_statement, Judge_answer, Judge_condition
from macm.thinker import Analysis_conditions, Think_thoughts, Think_Steps

GPT_CONFIG = {
    "model": "gpt-4-1106-preview",
    "temperature": 0.7,
    "n": 1,
    "max_tokens": 256
}

def check_condition(question, condition, n):
    for _ in range(n):
        if Judge_condition(question, condition).strip() == "False":
            return False
    return True

def check_statement(conditions, statement, n):
    for _ in range(n):
        answer = Judge_statement(conditions, statement)
        if "False" in answer or "false" in answer:
            return False
    return True

def check_answer(conditions, statement):
    if_got_answer = Judge_answer(conditions, statement)
    if "False" in if_got_answer or "false" in if_got_answer:
        return False
    return True

def check_if_got_answer(conditions, statement, n):
    for _ in range(n):
        if not check_answer(conditions, statement):
            return False
    return True    

def main(question, times, n, min_voters, max_voters):
    possible_answers = []
    try:
        voter_count = 0
        tie = True
        
        while tie or voter_count < min_voters:
            voter_count += 1
            print(f"\n# {voter_count} Thinker is analyzing the question...")
            conditions, objectives = Analysis_conditions(question, GPT_CONFIG)
            Initial_condition_numbers = len(conditions)
            
            for time in range(times):
                print(f"\n# {voter_count} Thinker is thinking new thoughts...")
                unchecked_conditions = Think_thoughts(conditions, objectives, GPT_CONFIG)
                checked_conditions = []
                for unchecked_condition in unchecked_conditions:
                    print(f"\n# {voter_count} Judge is checking conditions...")
                    if check_statement(conditions, unchecked_condition, n):
                        start = unchecked_condition.find("we can get: ")
                        if start != -1:
                            unchecked_condition = unchecked_condition[start + len("we can get: "):]
                            unchecked_condition = unchecked_condition.split("Reason:")[0]
                        checked_conditions.append(unchecked_condition)
                conditions = conditions + checked_conditions
                if check_if_got_answer(conditions, objectives, 1):
                    break
            
            print(f"\n# {voter_count} thinker is thinking steps...")
            steps = Think_Steps(conditions, objectives, GPT_CONFIG)
            
            print(f"\n# {voter_count} Executor is trying to calculate the answer...")
            final_answer = Execute_steps(conditions, objectives, steps)

            # Debug opcional
            print(f"\n[DEBUG] Raw final_answer:\n{final_answer}")
            with open("debug_output.txt", "w", encoding="utf-8") as f:
                f.write(final_answer)

            # Captura expressão algébrica (opcional)
            expr_match = re.search(r'Expression:\s*(.*)', final_answer)
            value_match = re.search(r'Value:\s*([-+]?\d*\.?\d+)', final_answer)

            expression = expr_match.group(1).strip() if expr_match else "Not found"
            value = value_match.group(1) if value_match else "No match found"

            print(f"\n[DEBUG] Extracted Expression: {expression}")
            print(f"[DEBUG] Extracted Value: {value}")

            possible_answers.append(value)
            
            if voter_count >= min_voters:
                counter = Counter(possible_answers)
                most_votes = counter.most_common(1)[0][1]  
                tie_count = len([x for x in counter.items() if x[1] == most_votes])
                
                tie = tie_count > 1
                if tie:
                    print("\nThere is a tie vote. We need to add another voter.")
                if voter_count >= max_voters:
                    print("\nReached maximum voter limit.")
                    break

        most_possible_answer, count = counter.most_common(1)[0]
        print(f"\nThe final answer is {most_possible_answer}")
        return most_possible_answer

    except Exception as e:
        print(f"Error processing file: {e}")

def evaluate_dataset(folder_path, times, n, limit=5):
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.json'):
                all_files.append(os.path.join(root, file))

    random.shuffle(all_files)

    for count, file_path in enumerate(all_files[:limit]):
        with open(file_path, 'r') as json_file:
            try:
                data = json.load(json_file)
                problem = data.get("problem")
                if problem:
                    print(f"#{count} Problem:\n", problem)
                    solution = data.get("solution")
                    print(f"#{count} Solution\n", solution)
                    main(problem, times, n)
            except json.JSONDecodeError:
                print(f"Error reading file {file_path}")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

if __name__ == "__main__":
    n = 1
    times = 2
    min_voters = 1
    max_voters = 1
    question = "Please do not immediately give the final answer.\n\nFirst, write a symbolic algebraic expression based on the following:\n\nAn employee has a base salary SB = 2000. They have 10 years of service, and their salary increases by 5% every 5 years. They also receive:\n- 10% qualification bonus (applied to the updated SB),\n- R$500 fixed bonus,\n- 10 overtime hours, calculated as: (SB / 220) × hours × 1.5.\n\nStep 1: Write the complete symbolic expression.\nStep 2: Plug in the values and simplify the final result.\n\nReturn **both** in the format:\n\nExpression: ...\nValue: ..."

    
    main(question, times, n, min_voters, max_voters)
