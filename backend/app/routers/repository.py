import json
import logging
import os
import shutil
from typing import Any, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.pipeline_cache import get_or_create_pipeline, invalidate_pipeline
from app.core.snapshot import (
    _build_tree_nodes,
    _ensure_snapshot_exists,
    _normalize_index_path,
    _save_snapshot_and_tree,
    _snapshot_dir,
    _to_repo_relative_paths,
    _tree_cache_path,
)
from app.database.database import SessionLocal
from app.dependencies.auth_dependency import get_current_user, get_db
from app.models.repository import Repository, RepoStatus
from app.models.user import User
from app.rag.ingestion import clone_repository
from app.rag.rag_pipeline import RAGConfig, RAGPipeline
from app.services.index_registry_service import get_index_path
from app.services.repository_service import create_repository, get_repository_if_indexed, update_repository_status

logger = logging.getLogger(__name__)

router = APIRouter()


class RepositoryListItem(BaseModel):
    id: int
    repo_url: str
    status: RepoStatus
    created_at: Any
    updated_at: Any


@router.post("/repository/add")
def add_repository(
    repo_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = create_repository(
        db=db,
        user_id=current_user.id,
        repo_url=repo_url,
    )

    return {
        "repository_id": repo.id,
        "repo_url": repo.repo_url,
        "status": repo.status,
        "sync_api_key": repo.sync_api_key,
    }


@router.get("/repository/list", response_model=List[RepositoryListItem])
def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repos = db.query(Repository).filter(
        Repository.user_id == current_user.id
    ).all()

    return repos


@router.get("/repository/status/{repo_id}")
def get_repository_status(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user.id,
    ).first()

    if not repo:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return {
        "repo_id": repo.id,
        "status": repo.status,
        "faiss_index_path": repo.faiss_index_path,
    }


@router.get("/repository/tree/{repo_id}")
def get_repository_tree(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = get_repository_if_indexed(db, repo_id, current_user.id)

    index_path = _normalize_index_path(repo.faiss_index_path)
    tree_cache = _tree_cache_path(index_path)

    _ensure_snapshot_exists(repo.repo_url, index_path)

    if os.path.exists(tree_cache):
        with open(tree_cache, "r", encoding="utf-8") as tree_file:
            tree = json.load(tree_file)
    else:
        rag_pipeline = get_or_create_pipeline(repo.faiss_index_path)
        if not rag_pipeline.vector_store:
            raise HTTPException(status_code=404, detail="Repository index not loaded")
        file_paths = [metadata.file_path for metadata in rag_pipeline.vector_store.metadata]
        relative_paths = _to_repo_relative_paths(file_paths)
        tree = _build_tree_nodes(relative_paths)

    return {
        "repo_id": repo.id,
        "tree": tree,
    }


@router.get("/repository/file-content/{repo_id}")
def get_repository_file_content(
    repo_id: int,
    file_path: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = get_repository_if_indexed(db, repo_id, current_user.id)

    index_path = _normalize_index_path(repo.faiss_index_path)
    _ensure_snapshot_exists(repo.repo_url, index_path)
    snapshot_dir = _snapshot_dir(index_path)

    normalized_relative = os.path.normpath(file_path).replace("\\", "/")
    if normalized_relative.startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid file path")

    absolute_path = os.path.abspath(os.path.join(snapshot_dir, normalized_relative))
    snapshot_root = os.path.abspath(snapshot_dir)
    if not absolute_path.startswith(snapshot_root + os.sep):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not os.path.exists(absolute_path) or os.path.isdir(absolute_path):
        raise HTTPException(status_code=404, detail="File not found")

    max_chars = 200_000
    try:
        with open(absolute_path, "r", encoding="utf-8") as file_handle:
            content = file_handle.read(max_chars + 1)
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="Binary file preview is not supported")

    truncated = len(content) > max_chars
    if truncated:
        content = content[:max_chars]

    return {
        "repo_id": repo.id,
        "file_path": normalized_relative,
        "content": content,
        "truncated": truncated,
    }


@router.post("/repository/update-status")
def update_repo_status(
    repo_id: int,
    status: RepoStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = update_repository_status(db, repo_id, current_user.id, status)

    if not repo:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return {"message": "Repository status updated"}


@router.get("/repository/index-path/{repo_id}")
def fetch_index_path(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path = get_index_path(db, repo_id, current_user.id)

    return {"index_path": path}


def background_index(repo_url: str, save_path: str, repo_id: int):
    db: Session = SessionLocal()
    temp_dir: str | None = None
    try:
        temp_dir = clone_repository(repo_url)
        rag_pipeline = RAGPipeline(RAGConfig())
        rag_pipeline.index_repository(temp_dir, save_path=save_path)
        _save_snapshot_and_tree(temp_dir, save_path)

        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if repo:
            repo.status = RepoStatus.INDEXED
            repo.faiss_index_path = save_path
            invalidate_pipeline(save_path)
            db.commit()
    except Exception as exc:
        logger.error("Background indexing failed for repo %s: %s", repo_id, exc, exc_info=True)
        db.rollback()
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if repo:
            repo.status = RepoStatus.FAILED
            db.commit()
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        db.close()


@router.post("/repository/index/{repo_id}")
def index_repository_endpoint(
    repo_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user.id,
    ).first()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    invalidate_pipeline(repo.faiss_index_path)

    repo.status = RepoStatus.INDEXING
    db.commit()

    index_path = os.path.abspath(f"indexes/repo_{repo_id}")
    os.makedirs("indexes", exist_ok=True)

    background_tasks.add_task(background_index, repo.repo_url, index_path, repo_id)

    return {"message": "Indexing started"}
