from typing import Optional, List, Dict
from ai.provider import LLMProvider
from ai.schemas import KnowledgeExplanationAI
from ai.prompts.knowledge import RAG_KNOWLEDGE_SYSTEM_PROMPT, build_rag_query_prompt
from services.learning_service import get_llm_provider
from rag.models import KnowledgeDocument, SearchResult, RAGContext
from rag.retrieval import KnowledgeRetriever
from rag.ingestion import KnowledgeStore, get_knowledge_store


class RAGEngine:
    """
    Orchestrates the Retrieval-Augmented Generation pipeline:
    Query -> Retrieve Knowledge -> Construct Grounded Context -> Generate Structured AI Explanation.
    """

    def __init__(
        self,
        retriever: Optional[KnowledgeRetriever] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.retriever = retriever or KnowledgeRetriever()
        self.llm_provider = llm_provider

    def build_context(self, search_results: List[SearchResult], query: str) -> RAGContext:
        """Construct structured context block from retrieved search results."""
        if not search_results:
            return RAGContext(
                query=query,
                context_text="",
                sources=[],
                relevance_scores={},
            )

        context_blocks = []
        sources = []
        scores: Dict[str, float] = {}

        for i, res in enumerate(search_results, 1):
            doc = res.document
            sources.append(doc)
            scores[doc.id] = res.score

            rules_formatted = "\n  * " + "\n  * ".join(doc.rules) if doc.rules else "  None specified"
            examples_formatted = "\n  - " + "\n  - ".join(doc.correct_examples[:3]) if doc.correct_examples else ""
            mistakes_formatted = "\n  ! " + "\n  ! ".join(doc.common_mistakes[:3]) if doc.common_mistakes else ""

            block = f"""--- Document #{i}: [{doc.id}] {doc.title} (Relevance: {int(res.score * 100)}%) ---
Category: {doc.category} | Topic: {doc.topic}
Summary: {doc.summary}
Rules:{rules_formatted}
Pedagogical Content:
{doc.content}
Correct Examples:{examples_formatted}
Common Pitfalls:{mistakes_formatted}
Source: {doc.source}
"""
            context_blocks.append(block)

        context_text = "\n\n".join(context_blocks)

        return RAGContext(
            query=query,
            context_text=context_text,
            sources=sources,
            relevance_scores=scores,
        )

    async def query(
        self,
        query_text: str,
        category: Optional[str] = None,
        target_word: Optional[str] = None,
        top_k: int = 3,
        min_threshold: float = 0.10,
        llm: Optional[LLMProvider] = None,
    ) -> tuple[KnowledgeExplanationAI, List[SearchResult]]:
        """
        Execute RAG query pipeline. Returns structured explanation and retrieved sources.
        """
        # 1. Retrieve relevant knowledge documents
        search_results = self.retriever.search(
            query=query_text,
            top_k=top_k,
            min_threshold=min_threshold,
            category=category,
        )

        # 2. Build augmented context
        rag_context = self.build_context(search_results, query=query_text)

        # 3. Build prompt
        prompt = build_rag_query_prompt(
            query=query_text,
            retrieved_context=rag_context.context_text,
            target_word=target_word,
            category=category,
        )

        provider = llm or self.llm_provider or get_llm_provider()

        # 4. Generate structured explanation via LLM
        try:
            explanation = await provider.generate_structured(
                prompt=prompt,
                response_schema=KnowledgeExplanationAI,
                system_prompt=RAG_KNOWLEDGE_SYSTEM_PROMPT,
                temperature=0.3,
            )
        except Exception:
            # Fallback deterministic response from top retrieved document if available
            if search_results:
                top_doc = search_results[0].document
                explanation = KnowledgeExplanationAI(
                    summary=top_doc.summary,
                    detailed_explanation=top_doc.content,
                    rule_applied=top_doc.rules[0] if top_doc.rules else top_doc.topic,
                    correct_usage=top_doc.correct_examples[:3],
                    incorrect_usage=top_doc.common_mistakes[:2],
                    learning_tip=f"Remember the key principle from {top_doc.title}: {top_doc.rules[0] if top_doc.rules else top_doc.summary}",
                    groundedness_confidence=round(search_results[0].score, 2),
                )
            else:
                explanation = KnowledgeExplanationAI(
                    summary="General English grammar and usage principles apply to this question.",
                    detailed_explanation="English grammatical rules govern word choice, tense agreement, and prepositional usage. Following standard collocations ensures clear and natural communication.",
                    rule_applied="Standard English Usage Principles",
                    correct_usage=[],
                    incorrect_usage=[],
                    learning_tip="Check for standard prepositional pairings and grammatical consistency.",
                    groundedness_confidence=0.5,
                )

        return explanation, search_results
