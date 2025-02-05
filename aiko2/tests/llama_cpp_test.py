from typing import Iterator
from llama_cpp import Llama
import time

def manual_inference():
    llm = Llama.from_pretrained(
        "bartowski/Llama-3.2-3B-Instruct-GGUF",
        filename="*Q6_K.gguf",
        verbose=True,
        n_ctx=10000,
        n_gpu_layers=-1,
        flash_attn=True
    )

    print("Model loaded. Enter prompts to generate completions.")
    print("Enter 'exit' to quit.")

    while True:
        prompt = input("Prompt: ")
        if prompt == "exit":
            break
        start_time = time.time()
        response = llm(
            prompt,
            max_tokens=4000,
            temperature=1.3
        )
        end_time = time.time()
        completion_tokens = int(response["usage"]["completion_tokens"])
        tps = completion_tokens / (end_time - start_time)
        tps = round(tps, 2)
        print(f"TPS: {tps}, Time: {round(end_time - start_time, 2)}s")
        print()
        print(response["choices"][0])
        print()

def test_chat_completion():
    llm = Llama.from_pretrained(
        "bartowski/Llama-3.2-3B-Instruct-GGUF",
        filename="*Q6_K.gguf",
        verbose=True,
        n_ctx=100000,
        n_gpu_layers=-1,
        flash_attn=True,
        n_threads=8
    )
    start_time = time.time()
    response = llm.create_chat_completion(
        messages = [
            {
                "role": "system", 
                "content": "You are a japanese fox-girl named Aiko and an expert in creative poetry."},
            {
                "role": "user",
                "content": "Write a poem about minecraft."
            }
        ],
        max_tokens=4000,
        temperature=1.3)
    
    end_time = time.time()
    print(response["choices"][0])

    completion_tokens = int(response["usage"]["completion_tokens"])
    tps = completion_tokens / (end_time - start_time)
    tps = round(tps, 2)
    print(f"Tokens per second: {tps}")

    print(f"Usage: {response['usage']}")
    print()




def test_basic_completion():
    llm = Llama.from_pretrained(
        "bartowski/Llama-3.2-3B-Instruct-GGUF",
        filename="*Q6_K.gguf",
    )
    output = llm(
        "Q: Name the planets in the solar system? A: ", # Prompt
        max_tokens=64, # Generate up to 32 tokens, set to None to generate up to the end of the context window
        stop=["Q:", "\n"], # Stop generating just before the model would generate a new question
        echo=True # Echo the prompt back in the output
    ) # Generate a completion, can also call create_completion

    print(output["choices"][0])


if __name__ == "__main__":
    #test_chat_completion()
    # test_basic_completion()
    manual_inference()
