import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables from the correct .env file
load_dotenv(".env")

# Retrieve the OpenAI API key from the .env file
API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Explain how AI works")
print(response.text)