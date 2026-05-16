import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth_router, chat_router, repository_router, sync_router

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI()

_dev_origins = [f"http://localhost:{port}" for port in range(3000, 3011)] + [
    f"http://127.0.0.1:{port}" for port in range(3000, 3011)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_dev_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(repository_router)
app.include_router(chat_router)
app.include_router(sync_router)