from typing import Optional

from app.rag.config import (
    ANTHROPIC_AVAILABLE,
    GROQ_AVAILABLE,
    OPENAI_AVAILABLE,
    RAGConfig,
    anthropic,
    groq_module,
    openai,
)


class LLMClient:
    """Unified interface for Groq, Anthropic, and OpenAI."""

    def __init__(self, config: RAGConfig):
        self.config = config
        self.provider = config.llm_provider
        self.client = None

        if self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise RuntimeError("anthropic library required. Install: pip install anthropic")
            if not config.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is not set.")
            self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)

        elif self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("openai library required. Install: pip install openai")
            if not config.openai_api_key:
                raise ValueError("OPENAI_API_KEY is not set.")
            self.client = openai.OpenAI(api_key=config.openai_api_key)

        elif self.provider == "groq":
            if not GROQ_AVAILABLE:
                raise RuntimeError("groq library required. Install: pip install groq")
            if not config.groq_api_key:
                raise ValueError("GROQ_API_KEY is not set.")
            self.client = groq_module.Groq(api_key=config.groq_api_key)

        else:
            raise ValueError(
                f"Unknown LLM provider: '{self.provider}'. "
                "Choose 'groq', 'anthropic', or 'openai'."
            )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from the configured LLM.
        """
        if self.provider == "anthropic":
            kwargs = {
                "model": self.config.llm_model,
                "max_tokens": self.config.llm_max_tokens,
                "temperature": self.config.llm_temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            response = self.client.messages.create(**kwargs)
            return response.content[0].text

        if self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=messages,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )
            return response.choices[0].message.content

        if self.provider == "groq":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            completion = self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=messages,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )
            return completion.choices[0].message.content

        return ""

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None):
        """Yields string tokens from the configured LLM streaming API."""
        if self.provider == "anthropic":
            kwargs = {
                "model": self.config.llm_model,
                "max_tokens": self.config.llm_max_tokens,
                "temperature": self.config.llm_temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            with self.client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text
            return

        if self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=messages,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
                stream=True,
            )
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
            return

        if self.provider == "groq":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            completion = self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=messages,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
                stream=True,
            )
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
            return
