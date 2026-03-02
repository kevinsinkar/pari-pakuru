import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API key from your .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("API Key not found. Make sure your .env file is set up.")
else:
    genai.configure(api_key=API_KEY)
    print("Available models that support 'generateContent':")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"- {model.name}")