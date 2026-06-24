"""RAG knowledge base using FAISS + sentence-transformers."""

import os
import re
import json
import hashlib
from pathlib import Path

import faiss
import numpy as np
from fastembed import TextEmbedding
from bs4 import BeautifulSoup


INDEX_DIR = Path(__file__).parent / "kb_index"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 200


class KnowledgeBase:
    def __init__(self):
        self.model: TextEmbedding | None = None
        self.index = None
        self.chunks = []
        self.metadata = []

    def load(self):
        """Load pre-built index from disk."""
        if not (INDEX_DIR / "index.faiss").exists():
            raise FileNotFoundError(
                "Knowledge base index not found. Run: python ingest.py"
            )
        self.model = TextEmbedding("BAAI/bge-small-en-v1.5")
        self.index = faiss.read_index(str(INDEX_DIR / "index.faiss"))
        with open(INDEX_DIR / "chunks.json", "r") as f:
            data = json.load(f)
            self.chunks = data["chunks"]
            self.metadata = data["metadata"]

    def search(self, query: str, top_k: int = 8) -> list[dict]:
        """Search the knowledge base for relevant chunks."""
        if self.index is None:
            self.load()
        query_embedding = list(self.model.embed([query]))
        distances, indices = self.index.search(
            np.array(query_embedding, dtype=np.float32), top_k
        )
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks):
                results.append({
                    "content": self.chunks[idx],
                    "source": self.metadata[idx]["source"],
                    "section": self.metadata[idx].get("section", ""),
                    "score": float(distances[0][i]),
                })
        return results


def extract_text_from_html(html_content: str) -> str:
    """Strip HTML tags and return clean text."""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def chunk_text(text: str, source: str) -> list[tuple[str, dict]]:
    """Split text into overlapping chunks with metadata."""
    # Split by sections (headers)
    sections = re.split(r'\n(?=#{1,4}\s)', text)
    chunks = []

    for section in sections:
        lines = section.strip().split("\n")
        section_title = lines[0].lstrip("#").strip() if lines else ""
        section_text = section.strip()

        if len(section_text) <= CHUNK_SIZE:
            if section_text:
                chunks.append((section_text, {"source": source, "section": section_title}))
        else:
            words = section_text.split()
            for i in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
                chunk = " ".join(words[i : i + CHUNK_SIZE])
                if chunk.strip():
                    chunks.append((chunk, {"source": source, "section": section_title}))

    return chunks


def build_index(content_dirs: list[str], output_dir: str = None):
    """Process all content files and build FAISS index."""
    if output_dir is None:
        output_dir = str(INDEX_DIR)

    os.makedirs(output_dir, exist_ok=True)
    all_chunks = []
    all_metadata = []

    for content_dir in content_dirs:
        content_path = Path(content_dir)
        if not content_path.exists():
            print(f"Warning: {content_dir} not found, skipping")
            continue

        for filepath in sorted(content_path.rglob("*")):
            if filepath.is_dir() or ".git" in str(filepath):
                continue
            if filepath.name.startswith(".") or filepath.name.startswith("~$"):
                continue

            relative = str(filepath.relative_to(content_path))

            try:
                if filepath.suffix == ".md":
                    text = filepath.read_text(encoding="utf-8", errors="ignore")
                elif filepath.suffix == ".html":
                    html = filepath.read_text(encoding="utf-8", errors="ignore")
                    text = extract_text_from_html(html)
                else:
                    continue

                if not text.strip():
                    continue

                source_label = f"{content_path.name}/{relative}"
                chunks = chunk_text(text, source_label)
                for chunk_text_item, meta in chunks:
                    all_chunks.append(chunk_text_item)
                    all_metadata.append(meta)
                print(f"  Processed: {source_label} ({len(chunks)} chunks)")

            except Exception as e:
                print(f"  Error processing {filepath}: {e}")

    if not all_chunks:
        print("No content found to index!")
        return

    print(f"\nEmbedding {len(all_chunks)} chunks...")
    model = TextEmbedding("BAAI/bge-small-en-v1.5")
    embeddings = np.array(list(model.embed(all_chunks)), dtype=np.float32)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))

    faiss.write_index(index, os.path.join(output_dir, "index.faiss"))
    with open(os.path.join(output_dir, "chunks.json"), "w") as f:
        json.dump({"chunks": all_chunks, "metadata": all_metadata}, f)

    print(f"Index built: {len(all_chunks)} chunks, dimension {dimension}")
    print(f"Saved to: {output_dir}")
