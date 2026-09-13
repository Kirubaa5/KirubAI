from typing import List, Dict, Optional, Set
from rag.models import KnowledgeDocument
from rag.embeddings import BaseEmbeddingProvider, DeterministicEmbeddingProvider
from rag.knowledge_data import CURATED_KNOWLEDGE_DOCUMENTS


class KnowledgeStore:
    """
    In-memory knowledge store managing curated knowledge documents,
    category indexes, and precomputed vector embeddings.
    """

    def __init__(self, embedding_provider: Optional[BaseEmbeddingProvider] = None):
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider()
        self._documents: Dict[str, KnowledgeDocument] = {}
        self._embeddings: Dict[str, List[float]] = {}
        self._categories: Dict[str, Set[str]] = {}  # category -> set of topics
        self._load_curated_knowledge()

    def _build_doc_searchable_text(self, doc: KnowledgeDocument) -> str:
        """Compose rich searchable text representing the document for embedding."""
        tags_str = " ".join(doc.tags)
        rules_str = " ".join(doc.rules)
        mistakes_str = " ".join(doc.common_mistakes)
        return f"{doc.title} {doc.topic} {doc.category} {tags_str} {rules_str} {doc.summary} {doc.content} {mistakes_str}"

    def _load_curated_knowledge(self) -> None:
        for doc in CURATED_KNOWLEDGE_DOCUMENTS:
            self.add_document(doc)

    def add_document(self, doc: KnowledgeDocument) -> None:
        """Add or update a knowledge document and index its vector embedding."""
        self._documents[doc.id] = doc

        # Index category and topic
        if doc.category not in self._categories:
            self._categories[doc.category] = set()
        self._categories[doc.category].add(doc.topic)

        # Generate and store embedding
        searchable_text = self._build_doc_searchable_text(doc)
        self._embeddings[doc.id] = self.embedding_provider.embed_text(searchable_text)

    def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve document by its ID."""
        return self._documents.get(doc_id)

    def get_all_documents(self) -> List[KnowledgeDocument]:
        """Retrieve all indexed documents."""
        return list(self._documents.values())

    def get_embedding(self, doc_id: str) -> Optional[List[float]]:
        """Retrieve precomputed embedding for document."""
        return self._embeddings.get(doc_id)

    def get_categories(self) -> Dict[str, List[str]]:
        """Retrieve all categories and their associated topics."""
        return {cat: sorted(list(topics)) for cat, topics in self._categories.items()}

    def count(self) -> int:
        return len(self._documents)


# Global singleton instance for app runtime
_KNOWLEDGE_STORE_INSTANCE: Optional[KnowledgeStore] = None


def get_knowledge_store() -> KnowledgeStore:
    """Get or create singleton KnowledgeStore instance."""
    global _KNOWLEDGE_STORE_INSTANCE
    if _KNOWLEDGE_STORE_INSTANCE is None:
        _KNOWLEDGE_STORE_INSTANCE = KnowledgeStore()
    return _KNOWLEDGE_STORE_INSTANCE
