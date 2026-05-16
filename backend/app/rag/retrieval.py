import re
from typing import Dict, List, Optional, Tuple


def _is_location_query(query: str) -> bool:
    query_lower = query.lower()
    has_where = "where" in query_lower
    has_symbol = any(
        token in query_lower
        for token in [
            "function",
            "funtion",
            "method",
            "handler",
            "authentication",
            "authenctication",
            "auth",
            "login",
            "signin",
            "register",
            "jwt",
            "token",
        ]
    )
    return has_where and has_symbol


def _is_repo_summary_query(query: str) -> bool:
    query_lower = query.lower()
    return any(
        term in query_lower
        for term in [
            "summarize",
            "summary",
            "overview",
            "architecture",
            "repo structure",
            "repository structure",
            "project structure",
            "explain the repo",
            "explain this repo",
            "how is this repo organized",
        ]
    )


def _query_prefers_python(query: str) -> bool:
    query_lower = query.lower()
    wants_python = bool(
        re.search(r"\bpython\b", query_lower)
        or re.search(r"\.py\b", query_lower)
        or "python file" in query_lower
        or "py file" in query_lower
    )
    if not wants_python:
        return False

    other_language_markers = [
        r"\bjavascript\b", r"\.js\b",
        r"\btypescript\b", r"\.ts\b", r"\.tsx\b",
        r"\bjava\b", r"\.java\b",
        r"\bgo\b", r"\.go\b",
        r"\brust\b", r"\.rs\b",
        r"\bcsharp\b", r"\bc#\b", r"\.cs\b",
        r"\bphp\b", r"\.php\b",
        r"\bruby\b", r"\.rb\b",
        r"\bswift\b", r"\.swift\b",
        r"\bkotlin\b", r"\.kt\b", r"\.kts\b",
        r"\bscala\b", r"\.scala\b",
    ]
    return not any(re.search(marker, query_lower) for marker in other_language_markers)


def _extract_file_hint(query: str) -> Optional[str]:
    pattern = (
        r"([A-Za-z0-9_\-./\\]+?\."
        r"(?:py|pyi|js|jsx|mjs|cjs|ts|tsx|java|kt|kts|scala|go|rs|c|h|cpp|cc|cxx|hpp|hh|hxx|"
        r"cs|php|rb|swift|m|mm|sh|bash|zsh|ps1|sql|yaml|yml|json|toml|ini|cfg|env|md))\b"
    )
    matches = re.findall(pattern, query, flags=re.IGNORECASE)
    if not matches:
        return None

    candidate = matches[-1].strip("`'\"()[]{}<>.,:;")
    return candidate.replace("\\", "/").lower() if candidate else None


def _is_file_explanation_query(query: str, file_hint: Optional[str]) -> bool:
    if not file_hint:
        return False

    query_lower = query.lower()
    explanation_markers = [
        "what does",
        "what is",
        "explain",
        "overview",
        "summary",
        "summarize",
        "describe",
        "purpose",
    ]
    return any(marker in query_lower for marker in explanation_markers)


def _extract_exact_search_term(query: str) -> Optional[str]:
    query_stripped = query.strip()
    query_lower = query_stripped.lower()

    quoted = re.findall(r"['\"]([^'\"]{2,})['\"]", query_stripped)
    if quoted:
        return quoted[0].strip()

    marker = "search for this statement"
    if marker in query_lower:
        idx = query_lower.find(marker)
        term = query_stripped[idx + len(marker):].strip(" :.-")
        if term:
            return term

    call_like = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*\s*\([^\)]{0,120}\))", query_stripped)
    if call_like:
        return call_like.group(1).strip()

    return None


def _build_location_answer(query: str, retrieved_chunks: List[Tuple], vector_store) -> Optional[str]:
    if not retrieved_chunks:
        return None

    query_tokens = [
        token
        for token in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", query.lower())
        if len(token) > 2 and token not in {"where", "function", "funtion", "method", "handler"}
    ]

    login_like = any(token.startswith("log") or token.startswith("auth") for token in query_tokens)
    patterns: List[re.Pattern[str]] = []
    if login_like:
        patterns.extend([
            re.compile(r"\bfunction\s+login\b", re.IGNORECASE),
            re.compile(r"\b(?:const|let|var)\s+login\s*=", re.IGNORECASE),
            re.compile(r"\blogin\s*[:=]\s*function\b", re.IGNORECASE),
            re.compile(r"\brouter\.(?:post|get)\s*\(\s*['\"]\/login['\"]", re.IGNORECASE),
            re.compile(r"\bapp\.(?:post|get)\s*\(\s*['\"]\/login['\"]", re.IGNORECASE),
            re.compile(r"\b(?:authenticate|authentication|auth)\b", re.IGNORECASE),
            re.compile(r"\brouter\.(?:post|get|use)\s*\(", re.IGNORECASE),
            re.compile(r"\bapp\.(?:post|get|use)\s*\(", re.IGNORECASE),
        ])

    if not patterns:
        for token in query_tokens:
            safe_token = re.escape(token)
            patterns.append(re.compile(rf"\b{safe_token}\b", re.IGNORECASE))

    scored_hits: List[Tuple[int, str, int, str]] = []
    for metadata, _score in retrieved_chunks:
        source_lines = metadata.source_text.splitlines()
        file_lower = metadata.file_path.lower()
        file_bonus = 0
        if any(token in file_lower for token in ["auth", "route", "login"]):
            file_bonus += 30
        elif any(token in file_lower for token in ["server", "controller", "handler"]):
            file_bonus += 15

        for line_offset, source_line in enumerate(source_lines):
            stripped = source_line.strip()
            if not stripped:
                continue
            if not any(pattern.search(source_line) for pattern in patterns):
                continue

            line_score = 0
            line_lower = stripped.lower()
            if re.search(r"\b(function|def|async\s+function)\b", line_lower):
                line_score += 25
            if re.search(r"\b(router|app)\.(post|get|use)\s*\(", line_lower):
                line_score += 30
            if re.search(r"\b(login|signin|register|auth|authenticate|jwt|token)\b", line_lower):
                line_score += 20
            if re.search(r"\bauth\s*:\s*\{", line_lower):
                line_score -= 15

            total_score = file_bonus + line_score
            line_number = metadata.start_line + line_offset
            scored_hits.append((total_score, metadata.file_path, line_number, stripped))

            if len(scored_hits) >= 20:
                break
        if len(scored_hits) >= 20:
            break

    if not scored_hits:
        return None

    scored_hits.sort(key=lambda item: item[0], reverse=True)

    deduped_hits: List[Tuple[str, int, str]] = []
    seen = set()
    for _score, file_path, line_number, snippet in scored_hits:
        dedupe_key = (file_path, line_number)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped_hits.append((file_path, line_number, snippet))
        if len(deduped_hits) >= 3:
            break

    formatted_hits = "\n".join(
        f"- {file_path}:{line_number} → {snippet[:140]}"
        for file_path, line_number, snippet in deduped_hits
    )
    return f"Likely location(s) for your function:\n{formatted_hits}"


def _build_exact_search_answer(term: str, vector_store) -> Optional[str]:
    if not vector_store or not getattr(vector_store, "metadata", None):
        return None

    needle = term.strip()
    if len(needle) < 2:
        return None

    needle_lower = needle.lower()
    hits: List[Tuple[str, int, str]] = []

    for metadata in vector_store.metadata:
        source_lines = metadata.source_text.splitlines()
        for line_offset, source_line in enumerate(source_lines):
            if needle_lower in source_line.lower():
                hits.append(
                    (metadata.file_path, metadata.start_line + line_offset, source_line.strip())
                )
                if len(hits) >= 8:
                    break
        if len(hits) >= 8:
            break

    if not hits:
        return None

    deduped_hits: List[Tuple[str, int, str]] = []
    seen = set()
    for file_path, line_number, snippet in hits:
        key = (file_path, line_number)
        if key in seen:
            continue
        seen.add(key)
        deduped_hits.append((file_path, line_number, snippet))
        if len(deduped_hits) >= 5:
            break

    formatted_hits = "\n".join(
        f"- {file_path}:{line_number} → {snippet[:180]}"
        for file_path, line_number, snippet in deduped_hits
    )
    return f"Found exact match(es) for '{needle}':\n{formatted_hits}"


def _build_fallback_answer(
    query: str,
    retrieved_chunks: List[Tuple],
    generation_error: Optional[str] = None,
) -> str:
    query_lower = query.lower()
    is_summary_query = any(
        term in query_lower
        for term in [
            "summarize",
            "summary",
            "overview",
            "architecture",
            "structure",
        ]
    )

    connectivity_hint = "LLM generation is currently unavailable."

    if not retrieved_chunks:
        return f"{connectivity_hint}\n\nNo relevant code context was retrieved."

    if is_summary_query:
        files = []
        for metadata, _score in retrieved_chunks:
            file_path = metadata.file_path
            if file_path not in files:
                files.append(file_path)
            if len(files) >= 8:
                break

        top_dirs = {}
        for file_path in files:
            normalized = file_path.replace("\\", "/")
            parts = [p for p in normalized.split("/") if p]
            key = parts[0] if parts else "root"
            top_dirs[key] = top_dirs.get(key, 0) + 1

        dir_summary = ", ".join(
            f"{name} ({count})" for name, count in sorted(top_dirs.items(), key=lambda x: x[0])
        ) or "unknown"
        formatted_files = "\n".join(f"- {path}" for path in files)

        return (
            f"{connectivity_hint}\n\n"
            "I could not produce a full natural-language summary, but I can infer a rough structure from retrieved files:\n"
            f"- Top-level areas seen: {dir_summary}\n"
            "- Example files:\n"
            f"{formatted_files}"
        )

    query_tokens = [
        token
        for token in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", query.lower())
        if len(token) > 2
    ]

    candidate_hits: List[Tuple[str, int, str]] = []
    for metadata, _score in retrieved_chunks:
        source_lines = metadata.source_text.splitlines()
        for line_offset, source_line in enumerate(source_lines):
            source_line_lower = source_line.lower()
            if query_tokens and not any(token in source_line_lower for token in query_tokens):
                continue

            if re.search(r"\b(login|signin|sign_in|authenticate|auth)\b", source_line_lower):
                line_number = metadata.start_line + line_offset
                candidate_hits.append(
                    (metadata.file_path, line_number, source_line.strip())
                )
                if len(candidate_hits) >= 3:
                    break
        if len(candidate_hits) >= 3:
            break

    if candidate_hits:
        formatted_hits = "\n".join(
            f"- {file_path}:{line_number} → {snippet[:160]}"
            for file_path, line_number, snippet in candidate_hits
        )
        return (
            "LLM generation failed, but I found likely login-related code locations:\n"
            f"{formatted_hits}"
        )

    top_files = []
    for metadata, _score in retrieved_chunks[:3]:
        top_files.append(f"- {metadata.file_path}:{metadata.start_line}")

    return (
        "LLM generation failed, but relevant code was retrieved. "
        "Start with these files:\n"
        + "\n".join(top_files)
    )
