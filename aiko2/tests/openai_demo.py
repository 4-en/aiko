import os
import openai
from dotenv import load_dotenv

# Load environment variables from the correct .env file
load_dotenv(".env")

# Retrieve the OpenAI API key from the .env file
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("❌ Missing OpenAI API Key. Run setup_env.py to configure it.")

# Initialize the OpenAI client (New API Format)
client = openai.OpenAI(api_key=API_KEY)

def chat_with_openai(prompt):
    """Uses OpenAI's latest API format to generate a response."""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You should act as the character Aiko, a cute and slightly cheeky fox girl."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

if __name__ == "__main__":
    user_input = input("Enter your message: ")
    print("\nAiko: " + chat_with_openai(user_input))