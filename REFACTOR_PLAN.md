# Refactor Plan

## Overview
Pure code-organization refactor with zero behavior changes. Follow the required execution order. No frontend, model, service, dependency, or index changes.

## Files To Be Created
- backend/app/core/pipeline_cache.py
  - Purpose: Hold shared pipeline cache state and helpers currently in main.py.
- backend/app/core/snapshot.py
  - Purpose: Hold snapshot and repo tree helpers currently in main.py.
- backend/app/routers/__init__.py
  - Purpose: Export routers for clean inclusion in main.py.
- backend/app/routers/auth.py
  - Purpose: Auth routes and request model split from main.py.
- backend/app/routers/repository.py
  - Purpose: Repository routes, request models, and background index task split from main.py.
- backend/app/routers/chat.py
  - Purpose: Chat routes and streaming helper split from main.py.
- backend/app/routers/sync.py
  - Purpose: Sync route and background sync task split from main.py.
- backend/app/rag/config.py
  - Purpose: RAG config/dataclasses and provider availability checks.
- backend/app/rag/llm_client.py
  - Purpose: LLM client abstraction split from rag_pipeline.py.
- backend/app/rag/retrieval.py
  - Purpose: Retrieval helper functions split from rag_pipeline.py.
- backend/scripts/interactive.py
  - Purpose: Move interactive_mode REPL out of core library.

## Files To Be Modified
- backend/app/main.py
  - Purpose: Keep only app init, CORS, env loading, router registration, logger.
- backend/app/rag/rag_pipeline.py
  - Purpose: Simplify to RAGPipeline, PromptBuilder, CLI; import split modules.
- backend/app/rag/__init__.py
  - Purpose: Explicit exports for RAGPipeline, RAGConfig, RAGResponse, RetrievalResult, LLMClient.
- backend/app/core/__init__.py
  - Purpose: Explicit exports for shared core helpers.
- backend/app/models/__init__.py
  - Purpose: Explicit exports for User, Repository, RepoStatus, ChatHistory.

## Files To Be Deleted
- None.

## Dead Code To Remove
- backend/app/rag/rag_pipeline.py
  - Remove _GEMINI_QUOTA_ERRORS constant.
  - Replace Ollama-specific fallback strings with generic message.
  - Remove CLI args for Ollama (choices and ollama-url; remove config arg).
  - Remove commented-out code blocks longer than 3 lines.
  - Remove any unused imports introduced by refactor.
- backend/app/main.py
  - Remove section header comment blocks (optional; per instruction remove for cleanliness).
  - Replace traceback.print_exc() with logger.error(..., exc_info=True) in background_index.
  - Remove any unused imports introduced by refactor.
- All touched files
  - Remove any bare print() debug statements.

## Import Changes
- main.py
  - Replace direct route definitions with `app.include_router()` imports from app.routers.
  - Import routers from app.routers (auth_router, repository_router, chat_router, sync_router).
- routers/*.py
  - Use absolute imports from app.* for dependencies, services, models, core helpers, rag pipeline.
  - Import get_or_create_pipeline, invalidate_pipeline from app.core.pipeline_cache.
  - Import snapshot helpers from app.core.snapshot.
- rag_pipeline.py
  - Import RAGConfig, RetrievalResult, RAGResponse from app.rag.config.
  - Import LLMClient from app.rag.llm_client.
  - Import retrieval helper functions from app.rag.retrieval.
- rag/__init__.py
  - Explicit re-exports per requirement.
- models/__init__.py
  - Explicit re-exports; remove wildcard usage.

## Execution Steps And Verification

### Step 1: Generate Plan (current step)
- Create REFACTOR_PLAN.md (done by this plan).
- Wait for confirmation before changes.

### Step 2: Create core/pipeline_cache.py
- Move cache dict, lock, normalize, get_or_create_pipeline, invalidate_pipeline.
- Verification: None yet.

### Step 3: Create core/snapshot.py
- Move snapshot/tree helpers from main.py.
- Verification: None yet.

### Step 4: Create rag/config.py
- Move RAGConfig, RetrievalResult, RAGResponse and provider availability checks.
- Verification: None yet.

### Step 5: Create rag/llm_client.py
- Move LLMClient using provider flags from config.py.
- Verification: None yet.

### Step 6: Create rag/retrieval.py
- Extract helper functions and update signatures to accept vector_store.
- Verification: None yet.

### Step 7: Update rag/rag_pipeline.py
- Keep PromptBuilder, RAGPipeline, CLI; import split modules.
- Remove dead code per Task 3 (Gemini, Ollama, comment blocks, debug prints, unused imports).
- Update query/query_stream to use retrieval helpers.
- Move interactive_mode to backend/scripts/interactive.py and update CLI to use it.
- Verification: None yet.

### Step 8: Verify app boot
- Run: uvicorn app.main:app --reload
- Must start clean with routes visible.

### Step 9: Create routers/auth.py
- Move RegisterRequest, /register, /login.
- Verification: None yet.

### Step 10: Create routers/repository.py
- Move RepositoryListItem, repository endpoints, background_index.
- Update traceback logging per Task 3.
- Verification: None yet.

### Step 11: Create routers/chat.py
- Move chat endpoints and stream event_generator helper.
- Verification: None yet.

### Step 12: Create routers/sync.py
- Move sync endpoint and background_sync_index task.
- Verification: None yet.

### Step 13: Update main.py
- Keep app init, CORS, load_dotenv, logger, include_router registrations.
- Remove section comments and unused imports.
- Verification: None yet.

### Step 14: Verify app boot
- Run: uvicorn app.main:app --reload
- Must start clean with routes visible.

### Step 15: Remove dead code
- Ensure Task 3 removals across touched files.
- Verification: None yet.

### Step 16: Clean up __init__.py files
- rag/__init__.py, routers/__init__.py, core/__init__.py, models/__init__.py.
- Verification: None yet.

### Step 17: Final verification
- Run: uvicorn app.main:app --reload
- Manual checks:
  - POST /register -> 200
  - POST /login -> access_token
  - POST /repository/add -> 200
  - GET /repository/list -> 200
  - POST /repository/index/{repo_id} -> starts indexing
  - POST /chat/query -> answer
  - POST /chat/stream -> streams tokens
  - POST /repository/sync/{repo_id} -> 200 or 409

## Notes On Behavior Preservation
- All endpoint paths, methods, request/response shapes preserved.
- No changes to RAG logic, embeddings, vector store, or chunking.
- Any potential behavior change will be flagged before proceeding.
