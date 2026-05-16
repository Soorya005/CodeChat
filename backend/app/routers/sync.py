import logging
import os
import shutil

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.pipeline_cache import invalidate_pipeline
from app.core.snapshot import _save_snapshot_and_tree
from app.database.database import SessionLocal
from app.dependencies.auth_dependency import get_db
from app.models.repository import Repository, RepoStatus
from app.rag.ingestion import clone_repository
from app.rag.rag_pipeline import RAGConfig, RAGPipeline

logger = logging.getLogger(__name__)

router = APIRouter()


def background_sync_index(repo_url: str, save_path: str, repo_id: int):
    logger.info("Starting background_sync_index for repo %s", repo_id)
    db: Session = SessionLocal()
    temp_dir: str | None = None
    temp_save_path = save_path + "_temp"
    old_save_path = save_path + "_old"

    try:
        temp_dir = clone_repository(repo_url)
        rag_pipeline = RAGPipeline(RAGConfig())
        rag_pipeline.index_repository(temp_dir, save_path=temp_save_path)
        _save_snapshot_and_tree(temp_dir, temp_save_path)

        if os.path.exists(save_path):
            os.rename(save_path, old_save_path)

        try:
            os.rename(temp_save_path, save_path)
        except Exception as swap_exc:
            logger.error(
                "Failed to move temp index to active path for repo %s. Recovering from _old.",
                repo_id,
            )
            if os.path.exists(old_save_path):
                os.rename(old_save_path, save_path)
            raise swap_exc

        if os.path.exists(old_save_path):
            shutil.rmtree(old_save_path, ignore_errors=True)

        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if repo:
            repo.status = RepoStatus.INDEXED
            repo.faiss_index_path = save_path
            db.commit()

        invalidate_pipeline(save_path)
        logger.info("Successfully completed atomic swap and re-indexing for repo %s", repo_id)

    except Exception as exc:
        logger.error("Background sync failed for repo %s: %s", repo_id, exc, exc_info=True)
        db.rollback()
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if repo:
            repo.status = RepoStatus.FAILED
            db.commit()
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(temp_save_path):
            shutil.rmtree(temp_save_path, ignore_errors=True)
        db.close()


@router.post("/repository/sync/{repo_id}")
def sync_repository(
    repo_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    api_key = authorization.split(" ")[1]

    repo = db.query(Repository).filter(Repository.id == repo_id).first()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if not repo.sync_api_key or repo.sync_api_key != api_key:
        raise HTTPException(status_code=403, detail="Invalid token")

    if repo.status == RepoStatus.INDEXING:
        raise HTTPException(status_code=409, detail="Indexing already in progress")

    repo.status = RepoStatus.INDEXING
    db.commit()

    index_path = os.path.abspath(f"indexes/repo_{repo_id}")
    os.makedirs("indexes", exist_ok=True)

    logger.info("Sync request received for repo %s. Queuing background_sync_index.", repo_id)
    background_tasks.add_task(background_sync_index, repo.repo_url, index_path, repo_id)

    return {"status": "queued", "message": "Repository re-indexing started"}
