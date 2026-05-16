import importlib
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

try:
    anthropic = importlib.import_module("anthropic")
    ANTHROPIC_AVAILABLE = True
except Exception:
    anthropic = None
    ANTHROPIC_AVAILABLE = False

try:
    openai = importlib.import_module("openai")
    OPENAI_AVAILABLE = True
except Exception:
    openai = None
    OPENAI_AVAILABLE = False

try:
    groq_module = importlib.import_module("groq")
    GROQ_AVAILABLE = True
except Exception:
    groq_module = None
    GROQ_AVAILABLE = False


@dataclass
class RAGConfig:
    """Configuration for the RAG pipeline."""
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: Optional[str] = None

    index_type: str = "flat"

    top_k: int = 8
    similarity_threshold: float = 0.0

    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1200

    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    def __post_init__(self):
        llm_provider = os.getenv("LLM_PROVIDER") or os.getenv("RAG_LLM_PROVIDER")
        if llm_provider:
            self.llm_provider = llm_provider.strip().lower()

        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.groq_api_key:
            self.groq_api_key = os.getenv("GROQ_API_KEY")

        groq_model_env = os.getenv("GROQ_MODEL")
        if groq_model_env:
            self.llm_model = groq_model_env
        else:
            llm_model = os.getenv("LLM_MODEL")
            if llm_model:
                self.llm_model = llm_model

        llm_temperature = os.getenv("LLM_TEMPERATURE")
        if llm_temperature:
            try:
                self.llm_temperature = float(llm_temperature)
            except ValueError:
                pass

        llm_max_tokens = os.getenv("LLM_MAX_TOKENS")
        if llm_max_tokens:
            try:
                self.llm_max_tokens = int(llm_max_tokens)
            except ValueError:
                pass

        rag_top_k = os.getenv("RAG_TOP_K")
        if rag_top_k:
            try:
                parsed_top_k = int(rag_top_k)
                if parsed_top_k > 0:
                    self.top_k = parsed_top_k
            except ValueError:
                pass


@dataclass
class RetrievalResult:
    """Result returned by RAGPipeline.retrieve()."""
    chunks: List[Tuple]
    query: str
    total_found: int


@dataclass
class RAGResponse:
    """Complete response from RAGPipeline.query()."""
    query: str
    answer: str
    retrieved_chunks: List[Tuple]
    context_used: str
    metadata: Dict
