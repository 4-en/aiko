import torch
from transformers import pipeline

article = "forsen.txt"
article_text = open(article, "r").read()

model_id = "meta-llama/Llama-3.2-3B-Instruct"

pipe = pipeline(
    "text-generation", 
    model=model_id, 
    torch_dtype=torch.bfloat16, 
    device_map="auto"
)

messages = [
    {"role": "system", "content": "You are a professional summarizer. Given a question or a topic, you need to provide a summary of a following text that answers the question or is relevant to the topic. Only reply with the summary."},
    {"role": "user", "content": "Who is Forsen?"},
    {"role": "user", "content": article_text}

]
outputs = pipe(
    messages,
    max_new_tokens=256,
    temperature=0.7
)

text = outputs[0]["generated_text"][-1]["content"]
print(text)
