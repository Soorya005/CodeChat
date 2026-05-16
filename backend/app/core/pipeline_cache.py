import os
from threading import Lock
from typing import Dict

from app.rag.rag_pipeline import RAGPipeline, RAGConfig

_pipeline_cache: Dict[str, RAGPipeline] = {}
_pipeline_cache_lock = Lock()


def _normalize_index_path(index_path: str) -> str:
    return os.path.abspath(index_path)


def get_or_create_pipeline(index_path: str) -> RAGPipeline:
    normalized_path = _normalize_index_path(index_path)

    with _pipeline_cache_lock:
        cached_pipeline = _pipeline_cache.get(normalized_path)
        if cached_pipeline:
            return cached_pipeline

    pipeline = RAGPipeline(RAGConfig())
    pipeline.load_index(normalized_path)

    with _pipeline_cache_lock:
        _pipeline_cache[normalized_path] = pipeline

    return pipeline


def invalidate_pipeline(index_path: str | None) -> None:
    if not index_path:
        return

    normalized_path = _normalize_index_path(index_path)
    with _pipeline_cache_lock:
        _pipeline_cache.pop(normalized_path, None)
