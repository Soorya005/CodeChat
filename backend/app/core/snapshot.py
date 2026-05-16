import json
import os
import shutil
from typing import Any, Dict, List

from app.rag.ingestion import clone_repository
from app.rag.rag_pipeline import RAGPipeline


def _normalize_index_path(index_path: str) -> str:
    return os.path.abspath(index_path)


def _snapshot_dir(index_path: str) -> str:
    return os.path.join(_normalize_index_path(index_path), "source_snapshot")


def _tree_cache_path(index_path: str) -> str:
    return os.path.join(_normalize_index_path(index_path), "repo_tree.json")


def _build_tree_from_filesystem(root_dir: str) -> List[Dict[str, Any]]:
    def build_node(current_path: str, rel_path: str = "") -> List[Dict[str, Any]]:
        entries = []
        with os.scandir(current_path) as iterator:
            for entry in iterator:
                if entry.name == ".git":
                    continue
                child_rel_path = f"{rel_path}/{entry.name}" if rel_path else entry.name
                if entry.is_dir(follow_symlinks=False):
                    entries.append(
                        {
                            "name": entry.name,
                            "path": child_rel_path,
                            "type": "directory",
                            "children": build_node(entry.path, child_rel_path),
                        }
                    )
                else:
                    entries.append(
                        {
                            "name": entry.name,
                            "path": child_rel_path,
                            "type": "file",
                        }
                    )

        directories = sorted(
            [entry for entry in entries if entry["type"] == "directory"],
            key=lambda entry: entry["name"].lower(),
        )
        files = sorted(
            [entry for entry in entries if entry["type"] == "file"],
            key=lambda entry: entry["name"].lower(),
        )
        return directories + files

    return build_node(root_dir)


def _save_snapshot_and_tree(source_dir: str, index_path: str) -> None:
    snapshot_dir = _snapshot_dir(index_path)
    tree_cache = _tree_cache_path(index_path)

    if os.path.exists(snapshot_dir):
        shutil.rmtree(snapshot_dir)

    shutil.copytree(source_dir, snapshot_dir, ignore=shutil.ignore_patterns(".git"))

    tree = _build_tree_from_filesystem(snapshot_dir)
    with open(tree_cache, "w", encoding="utf-8") as tree_file:
        json.dump(tree, tree_file)


def _ensure_snapshot_exists(repo_url: str, index_path: str) -> None:
    snapshot_dir = _snapshot_dir(index_path)
    tree_cache = _tree_cache_path(index_path)
    if os.path.exists(snapshot_dir) and os.path.exists(tree_cache):
        return

    temp_dir = clone_repository(repo_url)
    try:
        _save_snapshot_and_tree(temp_dir, index_path)
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def _to_repo_relative_paths(file_paths: List[str]) -> List[str]:
    normalized = [os.path.normpath(path) for path in file_paths if path]
    if not normalized:
        return []

    try:
        common_prefix = os.path.commonpath(normalized)
    except ValueError:
        common_prefix = ""

    relative_paths: List[str] = []
    for path in normalized:
        if common_prefix:
            rel_path = os.path.relpath(path, common_prefix)
        else:
            rel_path = os.path.basename(path)
        rel_path = rel_path.replace("\\", "/")
        if rel_path and rel_path != ".":
            relative_paths.append(rel_path)

    return relative_paths


def _build_tree_nodes(relative_paths: List[str]) -> List[Dict[str, Any]]:
    unique_paths = sorted(set(relative_paths))
    tree: Dict[str, Any] = {}

    for rel_path in unique_paths:
        parts = [part for part in rel_path.split("/") if part]
        if not parts:
            continue

        current = tree
        for index, part in enumerate(parts):
            is_file = index == len(parts) - 1
            if part not in current:
                current[part] = {
                    "type": "file" if is_file else "directory",
                    "children": {},
                }
            if not is_file:
                current = current[part]["children"]

    def convert(node: Dict[str, Any], prefix: str = "") -> List[Dict[str, Any]]:
        directories = []
        files = []

        for name in sorted(node.keys()):
            entry = node[name]
            entry_path = f"{prefix}/{name}" if prefix else name
            if entry["type"] == "directory":
                directories.append(
                    {
                        "name": name,
                        "path": entry_path,
                        "type": "directory",
                        "children": convert(entry["children"], entry_path),
                    }
                )
            else:
                files.append(
                    {
                        "name": name,
                        "path": entry_path,
                        "type": "file",
                    }
                )

        return directories + files

    return convert(tree)


def _get_common_prefix_for_repo(rag_pipeline: RAGPipeline) -> str:
    if not rag_pipeline.vector_store or not getattr(rag_pipeline.vector_store, "metadata", None):
        return ""
    paths = [m.file_path for m in rag_pipeline.vector_store.metadata if m.file_path]
    normalized = [os.path.normpath(p) for p in paths if p]
    if not normalized:
        return ""
    try:
        return os.path.commonpath(normalized)
    except ValueError:
        return ""


def _format_source_path(file_path: str, common_prefix: str) -> str:
    if not file_path:
        return ""
    if common_prefix:
        try:
            rel_path = os.path.relpath(file_path, common_prefix)
        except ValueError:
            rel_path = os.path.basename(file_path)
    else:
        rel_path = os.path.basename(file_path)
    rel_path = rel_path.replace("\\", "/")
    return rel_path if rel_path and rel_path != "." else file_path
