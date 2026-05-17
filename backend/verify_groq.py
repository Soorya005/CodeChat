import os
from dotenv import load_dotenv

def test_groq():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY is not set in your .env file.")
        return

    try:
        import groq
        client = groq.Groq(api_key=api_key)
        model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        print(f"Testing Groq connection using model: {model}...")

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly: GROQ_OK"}],
            temperature=0.0,
            max_tokens=10,
        )
        text = response.choices[0].message.content.strip()
        print(f"Groq responded: {text!r}")
    except ImportError:
        print("ERROR: Groq Python package is not installed. Run: pip install groq")
    except Exception as e:
        print(f"ERROR: Groq call failed: {e}")

if __name__ == "__main__":
    test_groq()
