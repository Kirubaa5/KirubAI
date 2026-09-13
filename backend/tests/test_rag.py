import pytest
import math
from rag.models import KnowledgeDocument
from rag.embeddings import DeterministicEmbeddingProvider, cosine_similarity
from rag.ingestion import KnowledgeStore
from rag.retrieval import KnowledgeRetriever
from rag.engine import RAGEngine
from ai.mock_provider import MockLLMProvider
from ai.schemas import KnowledgeExplanationAI


# ============================================================
# Unit Tests for Embeddings & Vector Math
# ============================================================

def test_deterministic_embedding_normalized():
    """Verify embedding produces deterministic vector with unit L2 norm."""
    embedder = DeterministicEmbeddingProvider(dimension=128)
    vec1 = embedder.embed_text("look forward to meeting you")
    vec2 = embedder.embed_text("look forward to meeting you")

    assert len(vec1) == 128
    assert vec1 == vec2  # Deterministic

    # Check L2 norm is ~1.0
    norm = math.sqrt(sum(x * x for x in vec1))
    assert math.isclose(norm, 1.0, rel_tol=1e-3)


def test_deterministic_embedding_empty():
    """Verify empty or whitespace strings return zero vector."""
    embedder = DeterministicEmbeddingProvider(dimension=128)
    vec = embedder.embed_text("   ")
    assert all(x == 0.0 for x in vec)


def test_cosine_similarity_relevance():
    """Verify semantic similarity calculation behaves predictably."""
    embedder = DeterministicEmbeddingProvider(dimension=128)
    v_query = embedder.embed_text("why is discuss about incorrect?")
    v_related = embedder.embed_text("transitive verbs discuss without redundant preposition about")
    v_unrelated = embedder.embed_text("astronomical planetary orbital trajectories")

    sim_related = cosine_similarity(v_query, v_related)
    sim_unrelated = cosine_similarity(v_query, v_unrelated)

    assert sim_related > sim_unrelated
    assert sim_related > 0.3


# ============================================================
# Unit Tests for Knowledge Store & Ingestion
# ============================================================

def test_knowledge_store_curated_data_loaded():
    """Verify default curated knowledge documents are loaded and indexed."""
    store = KnowledgeStore()
    assert store.count() >= 10

    # Verify specific documents
    doc_look = store.get_document("DOC-GRAM-001")
    assert doc_look is not None
    assert "Look forward to" in doc_look.title
    assert doc_look.category == "grammar"

    doc_make = store.get_document("DOC-COLL-001")
    assert doc_make is not None
    assert doc_make.category == "collocations"

    # Verify precomputed embeddings exist
    emb = store.get_embedding("DOC-GRAM-001")
    assert emb is not None
    assert len(emb) == 128


def test_knowledge_store_categories():
    """Verify categories and topics are indexed properly."""
    store = KnowledgeStore()
    categories = store.get_categories()

    assert "grammar" in categories
    assert "common_mistakes" in categories
    assert "collocations" in categories
    assert "learning_tips" in categories


def test_knowledge_store_add_document():
    """Verify custom documents can be dynamically indexed."""
    store = KnowledgeStore()
    initial_count = store.count()

    custom_doc = KnowledgeDocument(
        id="DOC-CUSTOM-001",
        title="Subjunctive Mood in Formal English",
        category="grammar",
        topic="Subjunctive Mood",
        content="In formal recommendations, use base form: 'I insist that he be present.'",
        summary="Use bare infinitive in formal that-clauses of recommendation.",
        tags=["subjunctive", "formal english"],
        rules=["Demand/Recommend + that + subject + base verb"],
        correct_examples=["I recommend that she study daily."],
        common_mistakes=["Incorrect: 'I recommend that she studies.'"],
        source="Custom Reference",
    )
    store.add_document(custom_doc)

    assert store.count() == initial_count + 1
    retrieved = store.get_document("DOC-CUSTOM-001")
    assert retrieved is not None
    assert retrieved.title == "Subjunctive Mood in Formal English"
    assert store.get_embedding("DOC-CUSTOM-001") is not None


# ============================================================
# Unit Tests for Retrieval & Search
# ============================================================

def test_retriever_search_look_forward_to():
    """Verify retrieval returns relevant document for 'look forward to' query."""
    store = KnowledgeStore()
    retriever = KnowledgeRetriever(store=store)

    results = retriever.search("Why do we say look forward to meeting instead of meet?", top_k=3)
    assert len(results) >= 1
    top_result = results[0]
    assert top_result.document.id == "DOC-GRAM-001"
    assert top_result.score > 0.3
    assert "look forward to" in top_result.matched_tags


def test_retriever_category_filter():
    """Verify category filtering restricts returned results."""
    store = KnowledgeStore()
    retriever = KnowledgeRetriever(store=store)

    results = retriever.search(
        "decision mistakes",
        category="collocations",
        top_k=3,
    )
    for r in results:
        assert r.document.category == "collocations"


def test_retriever_empty_query():
    """Verify empty query returns empty list."""
    retriever = KnowledgeRetriever()
    assert retriever.search("") == []
    assert retriever.search("   ") == []


# ============================================================
# Unit Tests for RAG Engine & AI Orchestration
# ============================================================

@pytest.mark.asyncio
async def test_rag_engine_query_execution():
    """Verify RAG engine retrieves knowledge and generates structured AI response."""
    mock_llm = MockLLMProvider()
    engine = RAGEngine(llm_provider=mock_llm)

    explanation, sources = await engine.query(
        query_text="Is it correct to say 'Let's discuss about the budget'?",
        category="grammar",
    )

    assert isinstance(explanation, KnowledgeExplanationAI)
    assert "Discuss" in explanation.summary or "transitive" in explanation.summary.lower()
    assert len(explanation.correct_usage) > 0
    assert len(explanation.incorrect_usage) > 0
    assert explanation.groundedness_confidence >= 0.8

    # Verify sources were retrieved and attached
    assert len(sources) >= 1
    assert any("DOC-GRAM-002" == s.document.id for s in sources)


# ============================================================
# API Endpoint Integration Tests
# ============================================================

def test_api_knowledge_query_success(client, auth_headers):
    """Test POST /api/v1/knowledge/query returns structured explanation and sources."""
    response = client.post(
        "/api/v1/knowledge/query",
        json={
            "query": "Why is 'I look forward to meet you' wrong?",
            "category": "grammar",
            "top_k": 3,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "Why is 'I look forward to meet you' wrong?"
    assert len(data["summary"]) > 0
    assert len(data["detailed_explanation"]) > 0
    assert len(data["rule_applied"]) > 0
    assert len(data["correct_usage"]) > 0
    assert len(data["incorrect_usage"]) > 0
    assert len(data["learning_tip"]) > 0
    assert data["groundedness_confidence"] > 0.0

    # Verify source list
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["id"] == "DOC-GRAM-001"
    assert data["sources"][0]["relevance_score"] > 0.0


def test_api_knowledge_categories(client, auth_headers):
    """Test GET /api/v1/knowledge/categories returns category catalog."""
    response = client.get("/api/v1/knowledge/categories", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "categories" in data
    assert "grammar" in data["categories"]
    assert "collocations" in data["categories"]
    assert data["total_documents"] >= 10


def test_api_knowledge_documents_list_and_filter(client, auth_headers):
    """Test GET /api/v1/knowledge/documents with category and search filter."""
    # 1. List all
    resp_all = client.get("/api/v1/knowledge/documents", headers=auth_headers)
    assert resp_all.status_code == 200
    all_data = resp_all.json()
    assert all_data["total"] >= 10

    # 2. Filter by category
    resp_cat = client.get("/api/v1/knowledge/documents?category=collocations", headers=auth_headers)
    assert resp_cat.status_code == 200
    cat_data = resp_cat.json()
    assert all(item["category"] == "collocations" for item in cat_data["items"])

    # 3. Search query filter
    resp_search = client.get("/api/v1/knowledge/documents?search=affect", headers=auth_headers)
    assert resp_search.status_code == 200
    search_data = resp_search.json()
    assert any("DOC-MIST-001" == item["id"] for item in search_data["items"])


def test_api_knowledge_document_detail(client, auth_headers):
    """Test GET /api/v1/knowledge/documents/{doc_id} returns single doc or 404."""
    resp = client.get("/api/v1/knowledge/documents/DOC-GRAM-001", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "DOC-GRAM-001"
    assert "Look forward to" in data["title"]
    assert len(data["rules"]) > 0

    resp_404 = client.get("/api/v1/knowledge/documents/DOC-NONEXISTENT", headers=auth_headers)
    assert resp_404.status_code == 404


def test_api_knowledge_unauthorized_rejected(client):
    """Test unauthenticated requests are rejected with 401."""
    assert client.post("/api/v1/knowledge/query", json={"query": "test"}).status_code == 401
    assert client.get("/api/v1/knowledge/categories").status_code == 401
    assert client.get("/api/v1/knowledge/documents").status_code == 401
    assert client.get("/api/v1/knowledge/documents/DOC-GRAM-001").status_code == 401
