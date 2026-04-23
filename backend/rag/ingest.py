from __future__ import annotations

from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from backend.config import settings


def _load_documents(docs_dir: Path):
    documents = []
    for file_path in docs_dir.glob("**/*"):
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            documents.extend(PyPDFLoader(str(file_path)).load())
        elif suffix in {".txt", ".md"}:
            documents.extend(TextLoader(str(file_path), encoding="utf-8").load())

    return documents


def is_ingested() -> bool:
    """True if the Chroma DB directory exists and contains its SQLite artifact."""
    db_dir = Path(settings.chroma_db_path)
    sqlite_file = db_dir / "chroma.sqlite3"
    return db_dir.is_dir() and sqlite_file.exists()


def ingest_docs() -> None:
    docs_dir = Path(settings.docs_path)
    docs_dir.mkdir(parents=True, exist_ok=True)

    documents = _load_documents(docs_dir)
    if not documents:
        print("No documents found. Add files to backend/docs and rerun ingest.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(model=settings.embedding_model)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=settings.chroma_db_path,
    )

    # Chroma <0.5 exposes persist(); newer versions persist automatically.
    if hasattr(vectorstore, "persist"):
        vectorstore.persist()

    print(f"Ingested {len(chunks)} chunks from {len(documents)} documents.")


if __name__ == "__main__":
    ingest_docs()
