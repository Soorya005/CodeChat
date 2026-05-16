import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.pipeline_cache import get_or_create_pipeline
from app.dependencies.auth_dependency import get_current_user, get_db
from app.models.user import User
from app.services.chat_service import get_repository_chats, get_user_chats, save_chat
from app.services.repository_service import get_repository_if_indexed

router = APIRouter()


@router.post("/chat/save")
def store_chat(
    repository_url: str,
    query_text: str,
    response_text: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = save_chat(
        db=db,
        user_id=current_user.id,
        repository_url=repository_url,
        query_text=query_text,
        response_text=response_text,
    )

    return {"message": "Chat saved", "chat_id": chat.id}


@router.get("/chat/history")
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chats = get_user_chats(db, current_user.id)

    return chats


@router.get("/chat/repository")
def get_repo_chat_history(
    repository_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chats = get_repository_chats(
        db,
        current_user.id,
        repository_url,
    )

    return chats


@router.post("/chat/query")
def query_repository(
    repo_id: int,
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = get_repository_if_indexed(db, repo_id, current_user.id)

    rag_pipeline = get_or_create_pipeline(repo.faiss_index_path)

    response = rag_pipeline.query(query)

    save_chat(
        db=db,
        user_id=current_user.id,
        repository_url=repo.repo_url,
        query_text=query,
        response_text=response.answer,
    )

    return {
        "answer": response.answer,
        "sources": [
            {
                "file": meta.file_path.replace("\\", "/"),
                "symbol": meta.symbol_name,
                "line": meta.start_line,
            }
            for meta, score in response.retrieved_chunks
        ],
    }


@router.post("/chat/stream")
def stream_query(
    repo_id: int,
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = get_repository_if_indexed(db, repo_id, current_user.id)
    rag_pipeline = get_or_create_pipeline(repo.faiss_index_path)

    sources_list, stream_generator = rag_pipeline.query_stream(query)

    def event_generator():
        answer = ""
        for token in stream_generator:
            answer += token
            yield json.dumps({"delta": token}) + "\n"

        save_chat(
            db=db,
            user_id=current_user.id,
            repository_url=repo.repo_url,
            query_text=query,
            response_text=answer,
        )

        final_sources = [
            {
                "file": meta.file_path.replace("\\", "/"),
                "symbol": meta.symbol_name,
                "line": meta.start_line,
            }
            for meta, score in sources_list
        ]

        yield json.dumps({"done": True, "answer": answer, "sources": final_sources}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
