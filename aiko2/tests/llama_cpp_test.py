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

    print(llm.chat_format)

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

def format_output(output: str) -> str:
    # replace /n in the output with actual newlines
    output = output.replace("\\n", "\n")
    return output

def test_chat_completion():
    # llm = Llama.from_pretrained(
    #     "unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF",
    #     filename="*Q4_K_M.gguf",
    #     verbose=False,
    #     n_ctx=100000,
    #     flash_attn=True,
    #     n_gpu_layers=-1
    # )
    # llm = Llama.from_pretrained(
    #     "unsloth/DeepSeek-R1-Distill-Qwen-14B-GGUF",
    #     filename="*Q4_K_M.gguf",
    #     verbose=False,
    #     n_ctx=100000,
    #     flash_attn=True,
    #     n_gpu_layers=-1
    # )
    llm = Llama.from_pretrained(
        "unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF",
        filename="*Q4_K_M.gguf",
        verbose=False,
        n_ctx=100000,
        flash_attn=True,
        n_gpu_layers=-1
    )

    start_time = time.time()
    response = llm.create_chat_completion(
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful Minecraft assistant. Assist the user with any requests."},
            {
                "role": "user",
                "content": "Write a list of ten detailed tips for beginners in Minecraft."
            }
        ],
        max_tokens=4000,
        temperature=0.0
    )
    
    end_time = time.time()
    content = response["choices"][0]["message"]["content"]

    # if there is a </think> tag, seperate it
    cot = ""
    message = ""
    if "</think>" in content:
        cot = content.split("</think>", 1)
        if len(cot) == 2:
            message = cot[1]
            cot = cot[0].replace("<think>", "")
        else:
            message = cot[0]
            cot = ""

    if cot:
        print("Chain of thought:")
        print(format_output(cot))
        print()
    print("Message:")
    print(format_output(message))



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
