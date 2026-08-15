"""RAG package exports with lazy service imports to keep pure helpers lightweight."""
from app.rag.text import chunk_text

def index_file(*args, **kwargs):
    from app.rag.service import index_file as _index_file
    return _index_file(*args, **kwargs)

def search(*args, **kwargs):
    from app.rag.service import search as _search
    return _search(*args, **kwargs)

__all__ = ["chunk_text", "index_file", "search"]
