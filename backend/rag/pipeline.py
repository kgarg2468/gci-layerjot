from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import List

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from backend.config import settings


def _docs_dir() -> Path:
    return Path(settings.docs_path)


@lru_cache(maxsize=1)
def _maybe_get_retriever():
    db_path = Path(settings.chroma_db_path)
    if not db_path.exists() or not settings.openai_api_key:
        return None

    embeddings = OpenAIEmbeddings(model=settings.embedding_model)
    vectorstore = Chroma(
        persist_directory=str(db_path),
        embedding_function=embeddings,
    )
    return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})


def _tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"\W+", text.lower()) if token]


def _fallback_text_search(query: str, top_k: int = 3) -> List[dict]:
    tokens = set(_tokenize(query))
    results: list[tuple[int, str, str]] = []

    for file_path in _docs_dir().glob("**/*"):
        if not file_path.is_file() or file_path.suffix.lower() not in {".txt", ".md"}:
            continue

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        score = sum(1 for token in tokens if token in content.lower())
        if score <= 0:
            continue

        snippet = content[:700].replace("\n", " ").strip()
        results.append((score, snippet, file_path.name))

    results.sort(key=lambda item: item[0], reverse=True)
    return [
        {"content": snippet, "source": source, "score": score}
        for score, snippet, source in results[:top_k]
    ]


def query_protocol_docs(query: str, top_k: int = 3) -> List[dict]:
    retriever = _maybe_get_retriever()
    if retriever is not None:
        try:
            docs = retriever.invoke(query)
            if docs:
                return [
                    {
                        "content": doc.page_content,
                        "source": doc.metadata.get("source", "unknown"),
                    }
                    for doc in docs[:top_k]
                ]
        except Exception:
            # Fall through to plain-text search.
            pass

    return _fallback_text_search(query=query, top_k=top_k)
