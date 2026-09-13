from typing import List, Optional
from rag.models import KnowledgeDocument, SearchResult
from rag.ingestion import KnowledgeStore, get_knowledge_store
from rag.embeddings import cosine_similarity


class KnowledgeRetriever:
    """
    Retrieval engine performing dense vector search, relevance thresholding,
    and category filtering across the knowledge store.
    """

    def __init__(self, store: Optional[KnowledgeStore] = None):
        self.store = store or get_knowledge_store()

    def search(
        self,
        query: str,
        top_k: int = 3,
        min_threshold: float = 0.10,
        category: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search knowledge base using dense cosine similarity and metadata filters.
        """
        if not query or not query.strip():
            return []

        query_text = query.strip()
        query_vec = self.store.embedding_provider.embed_text(query_text)
        query_words = set(query_text.lower().split())

        results: List[SearchResult] = []

        for doc in self.store.get_all_documents():
            # Category filter
            if category and category.lower() != "all" and doc.category.lower() != category.lower():
                continue

            # Topic filter
            if topic and doc.topic.lower() != topic.lower():
                continue

            doc_vec = self.store.get_embedding(doc.id)
            if not doc_vec:
                continue

            similarity = cosine_similarity(query_vec, doc_vec)

            # Check matching tags
            matched_tags = [t for t in doc.tags if t.lower() in query_text.lower() or any(w in t.lower() for w in query_words)]

            # Tag match boost (up to +0.15 for exact tag matches)
            boost = min(0.15, len(matched_tags) * 0.05)
            final_score = min(1.0, round(similarity + boost, 4))

            if final_score >= min_threshold:
                results.append(
                    SearchResult(
                        document=doc,
                        score=final_score,
                        matched_tags=matched_tags,
                    )
                )

        # Sort descending by similarity score
        results.sort(key=lambda r: r.score, reverse=True)

        return results[:top_k]
