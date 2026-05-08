import logging
import os
from dotenv import load_dotenv
from app.rag.rag_pipeline import LLMClient, RAGConfig

logging.basicConfig(level=logging.INFO)
load_dotenv()

def test_gemini():
    print("--- Testing Gemini integration ---")
    config = RAGConfig(llm_provider="gemini", llm_model="gemini-1.5-flash")
    print(f"Config provider: {config.llm_provider}")
    print(f"Config model: {config.llm_model}")
    
    try:
        client = LLMClient(config)
        print("LLMClient initialized successfully.")
        
        prompt = "Hello! Are you working? Please respond with 'YES' if you are Gemini."
        print(f"Sending prompt: {prompt}")
        
        response = client.generate(prompt)
        print(f"Response from Gemini: {response}")
        
        if "YES" in response.upper():
            print("✅ Gemini Integration Verified!")
        else:
            print("⚠️ Gemini responded, but not as expected. Check the output above.")
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    test_gemini()
