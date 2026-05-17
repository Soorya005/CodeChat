import logging

from app.rag.config import RAGConfig
from app.rag.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)


def run_interactive(index_path: str, config: RAGConfig) -> None:
    """Launch an interactive REPL for querying the indexed codebase."""
    pipeline = RAGPipeline(config)
    pipeline.load_index(index_path)

    border = "=" * 60
    print(f"\n{border}\nRAG Pipeline - Interactive Mode\n{border}")
    print("Commands: stats | filter <lang> | clear | quit\n" + border + "\n")

    current_filters = None

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "quit":
                print("Goodbye!")
                break
            if user_input.lower() == "stats":
                stats = pipeline.vector_store.get_stats()
                    print(
                        f"\nStats: {stats['total_chunks']} chunks | "
                        f"Languages: {stats['languages']} | "
                        f"Types: {stats['chunk_types']}"
                    )
                continue
            if user_input.lower().startswith("filter "):
                lang = user_input[7:].strip()
                current_filters = {"language": lang}
                print(f"Filtering by language: {lang}")
                continue
            if user_input.lower() == "clear":
                current_filters = None
                print("Filters cleared")
                continue

            response = pipeline.query(user_input, filters=current_filters)
            print(f"\nAssistant:\n{response.answer}")
            print(f"\nRetrieved {response.metadata['chunks_used']} chunk(s):")
            for i, (meta, score) in enumerate(response.retrieved_chunks[:3], 1):
                print(
                    f"   {i}. {meta.symbol_name} "
                    f"– {meta.file_path}:{meta.start_line} "
                    f"(score: {score:.3f})"
                )

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as exc:
            logger.error("[RAG Pipeline] Unhandled error: %s", exc, exc_info=True)
            print(f"Error: {exc}")
