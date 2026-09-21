import pytest
from fastapi.testclient import TestClient
from ai.validation import (
    is_circular_or_generic_definition,
    is_generic_contextual_meaning,
    has_generic_collocations,
    has_generic_examples,
    validate_vocabulary_explanation,
    validate_vocabulary_examples,
)
from ai.schemas import WordExplanationAI, ExampleSetAI, ConversationalExampleAI


class TestSemanticValidationUnit:
    def test_rejects_circular_and_generic_definitions(self):
        """Ensure circular and boilerplate definition templates are rejected."""
        # Generic adjective pattern
        assert is_circular_or_generic_definition(
            "frivolous",
            "Characterized by or exhibiting the qualities and nature of 'frivolous'.",
        )

        # Generic noun pattern
        assert is_circular_or_generic_definition(
            "behavior",
            "The state, quality, concept, or condition associated with 'behavior'.",
        )

        # Generic verb pattern
        assert is_circular_or_generic_definition(
            "hesitate",
            "To demonstrate, carry out, or engage in the action of 'hesitate'.",
        )

        # Authentic definitions must pass
        assert not is_circular_or_generic_definition(
            "frivolous",
            "Not having any serious purpose or value; carefree and superficial.",
        )
        assert not is_circular_or_generic_definition(
            "behavior",
            "The way in which one acts or conducts oneself, especially toward others.",
        )

    def test_rejects_generic_contextual_usage(self):
        """Ensure generic contextual boilerplate is rejected."""
        assert is_generic_contextual_meaning(
            "frivolous",
            "Used in professional, academic, and daily communication when expressing ideas involving 'frivolous'.",
        )

        assert not is_generic_contextual_meaning(
            "frivolous",
            "Used to describe actions, spending, lawsuits, or remarks that waste time or money on trivial matters.",
        )

    def test_rejects_generic_collocations(self):
        """Ensure mechanical collocation string templates are rejected."""
        generic_cols = ["highly frivolous", "truly frivolous", "frivolous approach", "frivolous impact"]
        assert has_generic_collocations("frivolous", generic_cols)

        authentic_cols = ["frivolous lawsuit", "frivolous spending", "frivolous remark", "dismiss as frivolous"]
        assert not has_generic_collocations("frivolous", authentic_cols)

    def test_rejects_generic_example_templates(self):
        """Ensure templated scenario sentences are rejected."""
        generic_examples = [
            ConversationalExampleAI(context_label="Workplace", example_text="In our team meeting, we discussed how 'frivolous' impacts our project roadmap and key deliverables."),
            ConversationalExampleAI(context_label="Meeting", example_text="The project lead highlighted 'frivolous' as an important consideration for the upcoming quarter."),
            ConversationalExampleAI(context_label="Interview", example_text="During the interview, the candidate explained how they approach 'frivolous' in collaborative environments."),
        ]
        assert has_generic_examples("frivolous", generic_examples)

        authentic_examples = [
            ConversationalExampleAI(context_label="Workplace", example_text="The legal department quickly dismissed the claim as a frivolous lawsuit."),
            ConversationalExampleAI(context_label="Friends", example_text="She warned her friend against frivolous spending when saving for a house deposit."),
            ConversationalExampleAI(context_label="Meeting", example_text="The board refused to entertain frivolous suggestions during the annual budget review."),
        ]
        assert not has_generic_examples("frivolous", authentic_examples)


@pytest.mark.asyncio
class TestVocabularyContentBugFix:
    async def test_frivolous_and_behavior_receive_word_specific_content(self, client: TestClient, auth_headers):
        """Verify 'frivolous' and 'behavior' receive distinct, non-circular, authentic semantic content."""
        # 1. Add words
        res_f = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "frivolous"})
        res_b = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "behavior"})
        assert res_f.status_code == 201
        assert res_b.status_code == 201
        id_f = res_f.json()["id"]
        id_b = res_b.json()["id"]

        # 2. Fetch learning content
        learn_f = client.get(f"/api/v1/vocabulary/{id_f}/learn", headers=auth_headers).json()
        learn_b = client.get(f"/api/v1/vocabulary/{id_b}/learn", headers=auth_headers).json()

        # 3. Verify 'frivolous' details
        det_f = learn_f["details"]
        assert det_f["part_of_speech"] == "adjective"
        assert "not having any serious purpose" in det_f["simple_meaning"].lower() or "trivial" in det_f["simple_meaning"].lower() or "superficial" in det_f["simple_meaning"].lower()
        # Must not contain generic template phrases
        assert "qualities and nature of" not in det_f["simple_meaning"].lower()
        assert "when expressing ideas involving" not in det_f["contextual_meaning"].lower()
        # Collocations
        assert any("lawsuit" in col.lower() or "spending" in col.lower() for col in det_f["collocations"])
        assert "highly frivolous" not in det_f["collocations"]
        assert "truly frivolous" not in det_f["collocations"]
        # Examples
        exs_f = learn_f["examples"]
        assert len(exs_f) == 10
        ex_f_texts = " ".join(e["example_text"].lower() for e in exs_f)
        assert "impacts our project roadmap" not in ex_f_texts
        assert "frivolous lawsuit" in ex_f_texts or "frivolous spending" in ex_f_texts

        # 4. Verify 'behavior' details
        det_b = learn_b["details"]
        assert det_b["part_of_speech"] == "noun"
        assert "way in which one acts" in det_b["simple_meaning"].lower() or "conduct" in det_b["simple_meaning"].lower()
        # Must not contain generic template phrases
        assert "concept, or condition associated with" not in det_b["simple_meaning"].lower()
        assert "when expressing ideas involving" not in det_b["contextual_meaning"].lower()
        # Collocations
        assert any("acceptable" in col.lower() or "change" in col.lower() or "aggressive" in col.lower() or "pattern" in col.lower() for col in det_b["collocations"])
        assert "experience behavior" not in det_b["collocations"]
        assert "manage behavior" not in det_b["collocations"]
        # Examples
        exs_b = learn_b["examples"]
        assert len(exs_b) == 10
        ex_b_texts = " ".join(e["example_text"].lower() for e in exs_b)
        assert "impacts our project roadmap" not in ex_b_texts
        assert "behavior" in ex_b_texts

        # 5. Definitions, usage, collocations, and examples must fundamentally differ
        assert det_f["simple_meaning"] != det_b["simple_meaning"]
        assert det_f["contextual_meaning"] != det_b["contextual_meaning"]
        assert det_f["collocations"] != det_b["collocations"]
        assert exs_f[0]["example_text"] != exs_b[0]["example_text"]

    async def test_unrelated_words_across_parts_of_speech(self, client: TestClient, auth_headers):
        """Verify additional words (candid [adj], leverage [verb]) receive rich distinct linguistic content."""
        res_c = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "candid"})
        res_l = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "leverage"})
        assert res_c.status_code == 201
        assert res_l.status_code == 201

        learn_c = client.get(f"/api/v1/vocabulary/{res_c.json()['id']}/learn", headers=auth_headers).json()
        learn_l = client.get(f"/api/v1/vocabulary/{res_l.json()['id']}/learn", headers=auth_headers).json()

        # Candid (Adjective)
        assert learn_c["details"]["part_of_speech"] == "adjective"
        assert any(w in learn_c["details"]["simple_meaning"].lower() for w in ["truthful", "straightforward", "frank", "honest"])
        assert "qualities and nature of" not in learn_c["details"]["simple_meaning"].lower()
        assert any("feedback" in col.lower() or "discussion" in col.lower() for col in learn_c["details"]["collocations"])

        # Leverage (Verb)
        assert learn_c["details"]["simple_meaning"] != learn_l["details"]["simple_meaning"]
        assert any(w in learn_l["details"]["simple_meaning"].lower() for w in ["advantage", "utilize", "use"])
        assert "action of" not in learn_l["details"]["simple_meaning"].lower()
        assert any("technology" in col.lower() or "data" in col.lower() or "strengths" in col.lower() for col in learn_l["details"]["collocations"])

    async def test_unknown_word_in_mock_mode_returns_explicit_unavailable_error(self, client: TestClient, auth_headers):
        """Verify arbitrary unknown words in mock mode do NOT fabricate generic boilerplate and instead return 503."""
        res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "quizzaciously"})
        assert res.status_code == 201
        vocab_id = res.json()["id"]

        # Call learn endpoint for an unknown word without real LLM provider
        learn_res = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
        assert learn_res.status_code == 503
        err_detail = learn_res.json()["detail"]
        assert "not available in mock mode" in err_detail or "active LLM provider" in err_detail

    async def test_stale_generic_records_in_db_are_upgraded_on_learn(self, client: TestClient, auth_headers, db_session, test_user):
        """Verify previously stored generic records are detected as stale and replaced with authentic content."""
        from models.vocabulary import Vocabulary, WordDetails, VocabularyExample

        vocab = Vocabulary(
            user_id=test_user.id,
            word="frivolous",
            status="practiced",
            mastery_score=0.6,
        )
        db_session.add(vocab)
        db_session.commit()
        db_session.refresh(vocab)

        # Inject legacy bad generic data directly into DB
        bad_details = WordDetails(
            vocabulary_id=vocab.id,
            simple_meaning="Characterized by or exhibiting the qualities and nature of 'frivolous'.",
            contextual_meaning="Used in professional, academic, and daily communication when expressing ideas involving 'frivolous'.",
            part_of_speech="adjective",
            pronunciation_text="/frivolous/",
            synonyms=[],
            antonyms=[],
            word_forms={"base": "frivolous"},
            collocations=["highly frivolous", "truly frivolous", "frivolous approach", "frivolous impact"],
            cefr_level="B1",
            difficulty_score=5.0,
        )
        bad_example = VocabularyExample(
            vocabulary_id=vocab.id,
            example_text="In our team meeting, we discussed how 'frivolous' impacts our project roadmap and key deliverables.",
            context_label="Workplace",
            order_index=0,
        )
        db_session.add(bad_details)
        db_session.add(bad_example)
        db_session.commit()

        # Calling learn must detect the stale data and upgrade it with authentic curated data
        learn_res = client.get(f"/api/v1/vocabulary/{vocab.id}/learn", headers=auth_headers)
        assert learn_res.status_code == 200
        data = learn_res.json()

        # Progress preserved
        assert data["status"] == "practiced"
        assert data["mastery_score"] == 0.6

        # Generic data replaced
        assert "qualities and nature of" not in data["details"]["simple_meaning"]
        assert "Not having any serious purpose" in data["details"]["simple_meaning"] or "superficial" in data["details"]["simple_meaning"]
        assert "frivolous lawsuit" in data["details"]["collocations"]
        assert len(data["examples"]) == 10
        assert "impacts our project roadmap" not in data["examples"][0]["example_text"]
