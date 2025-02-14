from typing import Iterator
from llama_cpp import Llama
import time

# some llms for later
# bartowski/Llama-3.2-3B-Instruct-GGUF, *Q6_K.gguf
# unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF, *Q4_K_M.gguf
# unsloth/DeepSeek-R1-Distill-Qwen-14B-GGUF, *Q4_K_M.gguf
# unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF, *Q4_K_M.gguf
# unsloth/DeepSeek-R1-Distill-Qwen-3B-GGUF, *Q4_K_M.gguf
# bartowski/NousResearch_DeepHermes-3-Llama-3-8B-Preview-GGUF, *Q4_K_M.gguf

def custom_llama3_converter(chat: list[dict]) -> str:
    """
    Test custom chat converter for llama-3 based models

    <|begin_of_text|><|start_header_id|>system<|end_header_id|>
    {system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>
    {prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """
    parts = []
    # parts.append("<|begin_of_text|>")
    is_last_assistant = False
    for i, message in enumerate(chat):
        role = message["role"]
        is_last_assistant = role == "assistant" and i == len(chat) - 1

        content = message["content"]
        parts.append(f"<|start_header_id|>{role}<|end_header_id|>")
        parts.append(content)

        # inject assistant response and leave open ended if last message is from assistant
        if not is_last_assistant:
            parts.append("<|eot_id|>")
    
    if not is_last_assistant:
        parts.append("<|start_header_id|>assistant<|end_header_id|>")

    return "".join(parts)
        


def create_message(role: str, content: str) -> dict:
    return {
        "role": role,
        "content": content
    }

def manual_inference():
    llm = Llama.from_pretrained(
        "bartowski/NousResearch_DeepHermes-3-Llama-3-8B-Preview-GGUF",
        filename="*Q4_K_M.gguf",
        verbose=False,
        n_ctx=10000,
        n_gpu_layers=-1,
        flash_attn=True
    )

    # print(llm.chat_format)

    print("Model loaded. Enter prompts to generate completions.")
    print("Enter 'exit' to quit.")

    messages = []

    instruction = input("Instruction: ")
    instruction = instruction or "You are a deep thinking AI, you may use extremely long chains of thought to deeply consider the problem and deliberate with yourself via systematic reasoning processes to help come to a correct solution prior to answering. You should enclose your thoughts and internal monologue inside <think> </think> tags, and then provide your solution or response to the problem."

    messages.append(create_message("system", instruction))

    while True:
        prompt = input("Prompt: ")
        if prompt == "exit":
            break

        inject = ""
        if "::" in prompt:
            parts = prompt.split("::")
            prompt = parts[0]
            inject = parts[1]

        messages.append(create_message("user", prompt))

        if inject:
            print("Injecting:", inject)
            messages.append(create_message("assistant", "<think>" + inject))

        message_str = custom_llama3_converter(messages)
        start_time = time.time()
        response = llm(
            prompt=message_str,
            max_tokens=4000,
            temperature=1.2
        )

        end_time = time.time()
        completion_tokens = int(response["usage"]["completion_tokens"])
        tps = completion_tokens / (end_time - start_time)
        tps = round(tps, 2)
        print(f"TPS: {tps}, Time: {round(end_time - start_time, 2)}s")
        print()
        content = response["choices"][0]["text"]
        print(format_output(content))
        print()

        messages.append(create_message("assistant", inject+content))

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
