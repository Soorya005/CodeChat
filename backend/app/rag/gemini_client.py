import os
import warnings
# Suppress the google-generativeai deprecation notice until venv is rebuilt with google-genai
warnings.filterwarnings("ignore", category=FutureWarning, module="google")
import google.generativeai as genai
from typing import Optional

class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = self.model.generate_content(full_prompt)
        return response.text
