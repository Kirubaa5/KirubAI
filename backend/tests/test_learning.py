import pytest


@pytest.mark.asyncio
async def test_get_learning_content_generates_and_caches(client, auth_headers):
    # 1. Add word
    create_res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "hesitate"})
    assert create_res.status_code == 201
    vocab_id = create_res.json()["id"]

    # 2. Call learn endpoint
    learn_res = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
    assert learn_res.status_code == 200
    data = learn_res.json()

    assert data["word"] == "hesitate"
    assert data["details"] is not None
    assert "simple_meaning" in data["details"]
    assert len(data["details"]["synonyms"]) > 0
    assert len(data["details"]["collocations"]) > 0
    assert data["details"]["cefr_level"] == "B1"
    assert len(data["examples"]) == 10

    # 3. Call again to verify it returns cached data without error
    second_learn_res = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
    assert second_learn_res.status_code == 200
    assert len(second_learn_res.json()["examples"]) == 10


def test_mark_word_learned(client, auth_headers):
    # 1. Add word
    create_res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "persevere"})
    vocab_id = create_res.json()["id"]
    assert create_res.json()["status"] == "new"

    # 2. Mark learned
    res = client.post(f"/api/v1/vocabulary/{vocab_id}/mark-learned", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "learned"
    assert data["mastery_score"] > 0


@pytest.mark.asyncio
async def test_distinct_words_receive_distinct_ai_content(client, auth_headers):
    """Regression test: Ensure different words (hesitate, vividly, hassle) do NOT get identical content."""
    # 1. Add three distinct words
    hesitate_res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "hesitate"})
    vividly_res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "vividly"})
    hassle_res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "hassle"})

    assert hesitate_res.status_code == 201
    assert vividly_res.status_code == 201
    assert hassle_res.status_code == 201

    hesitate_id = hesitate_res.json()["id"]
    vividly_id = vividly_res.json()["id"]
    hassle_id = hassle_res.json()["id"]

    # 2. Fetch learning content for all three
    hesitate_learn = client.get(f"/api/v1/vocabulary/{hesitate_id}/learn", headers=auth_headers).json()
    vividly_learn = client.get(f"/api/v1/vocabulary/{vividly_id}/learn", headers=auth_headers).json()
    hassle_learn = client.get(f"/api/v1/vocabulary/{hassle_id}/learn", headers=auth_headers).json()

    # 3. Assert words receive fundamentally different definitions
    h_meaning = hesitate_learn["details"]["simple_meaning"]
    v_meaning = vividly_learn["details"]["simple_meaning"]
    ha_meaning = hassle_learn["details"]["simple_meaning"]

    assert h_meaning != v_meaning, "vividly must not have the definition of hesitate"
    assert h_meaning != ha_meaning, "hassle must not have the definition of hesitate"
    assert v_meaning != ha_meaning, "vividly and hassle must have different definitions"

    # 4. Assert correct parts of speech
    assert hesitate_learn["details"]["part_of_speech"] == "verb"
    assert vividly_learn["details"]["part_of_speech"] == "adverb"
    assert hassle_learn["details"]["part_of_speech"] == "noun"

    # 5. Assert distinct pronunciations
    assert hesitate_learn["details"]["pronunciation_text"] != vividly_learn["details"]["pronunciation_text"]
    assert "VIV" in vividly_learn["details"]["pronunciation_text"]
    assert "HASS" in hassle_learn["details"]["pronunciation_text"]

    # 6. Assert correct, non-mangled word forms (no "vividlytion" or "hassletion")
    v_forms = vividly_learn["details"]["word_forms"]
    ha_forms = hassle_learn["details"]["word_forms"]
    assert "vividlytion" not in str(v_forms)
    assert "hassletion" not in str(ha_forms)
    assert v_forms.get("adverb") == "vividly"
    assert v_forms.get("adjective") == "vivid"

    # 7. Assert distinct contextual examples
    h_ex0 = hesitate_learn["examples"][0]["example_text"]
    v_ex0 = vividly_learn["examples"][0]["example_text"]
    ha_ex0 = hassle_learn["examples"][0]["example_text"]

    assert h_ex0 != v_ex0
    assert "vividly" in v_ex0.lower()
    assert "hesitate" not in v_ex0.lower()
    assert "hassle" in ha_ex0.lower()
    assert "hesitate" not in ha_ex0.lower()


@pytest.mark.asyncio
async def test_unknown_word_does_not_inherit_hesitate_semantics(client, auth_headers):
    """Ensure arbitrary new words fall back gracefully without inheriting 'hesitate' definition."""
    res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "serendipity"})
    assert res.status_code == 201
    vocab_id = res.json()["id"]

    learn = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers).json()
    meaning = learn["details"]["simple_meaning"]

    # Must not contain pause/hesitate definition
    assert "pause before saying" not in meaning.lower()
    assert "hesitat" not in str(learn["details"]).lower()


@pytest.mark.asyncio
async def test_fear_receives_natural_and_non_generic_content(client, auth_headers):
    """Ensure 'fear' receives authentic definitions, synonyms, and natural conversational examples."""
    res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "fear"})
    assert res.status_code == 201
    vocab_id = res.json()["id"]

    learn = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers).json()
    details = learn["details"]
    examples = learn["examples"]

    # 1. Must not receive template/meta phrases
    assert "general meaning, usage, and definition" not in details["simple_meaning"].lower()
    assert "term related to" not in str(details["synonyms"]).lower()
    assert "concept of fear" not in str(details["synonyms"]).lower()

    # 2. Must receive meaningful emotional definition
    assert any(w in details["simple_meaning"].lower() for w in ["emotion", "danger", "threat", "harm"])
    assert "FEER" in details["pronunciation_text"]

    # 3. Must have valid synonyms and antonyms
    assert any(s in ["dread", "anxiety", "apprehension", "terror", "fright"] for s in details["synonyms"])
    assert any(a in ["courage", "bravery", "confidence", "fearlessness"] for a in details["antonyms"])

    # 4. Examples must genuinely use 'fear' naturally in varied contexts
    assert len(examples) == 10
    for ex in examples:
        assert "fear" in ex["example_text"].lower()
        # Ensure examples are not generic meta-sentences
        assert "used 'fear' accurately" not in ex["example_text"]
        assert "applied to our current workflow" not in ex["example_text"]


@pytest.mark.asyncio
async def test_unknown_word_safe_structure_and_no_hallucinations(client, auth_headers):
    """Ensure words return clean, authentic linguistic structures without template hallucinations."""
    res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "unprecedentedly"})
    assert res.status_code == 201
    vocab_id = res.json()["id"]

    learn = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers).json()
    details = learn["details"]

    # Suffix inference / dictionary identifies adverb
    assert details["part_of_speech"] == "adverb"

    # Authentic semantic synonyms
    assert any(s in details["synonyms"] for s in ["extraordinarily", "exceptionally", "incomparably", "uniquely", "phenomenally"])
    assert "term related to" not in str(details["synonyms"])
    assert "concept of" not in str(details["synonyms"])

    # Safe word forms without fake suffixes like 'unprecedentedlytion'
    assert "unprecedentedlytion" not in str(details["word_forms"])
    assert details["word_forms"].get("adverb") == "unprecedentedly"



@pytest.mark.asyncio
async def test_resilient_receives_rich_semantic_content(client, auth_headers):
    """Ensure 'resilient' receives rich, accurate semantic content and not generic templates."""
    res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "resilient"})
    assert res.status_code == 201
    vocab_id = res.json()["id"]

    learn_res = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
    assert learn_res.status_code == 200
    data = learn_res.json()

    details = data["details"]
    examples = data["examples"]

    # 1. Verify rich semantic definition
    assert "withstand or recover quickly" in details["simple_meaning"].lower()
    assert details["part_of_speech"] == "adjective"
    assert "ri-ZIL-yunt" in details["pronunciation_text"]
    assert details["cefr_level"] == "B2"
    assert details["difficulty_score"] == 6.0

    # 2. Verify synonyms and antonyms
    assert "tough" in details["synonyms"] or "durable" in details["synonyms"] or "adaptable" in details["synonyms"]
    assert "fragile" in details["antonyms"] or "vulnerable" in details["antonyms"]

    # 3. Verify word forms and collocations
    assert details["word_forms"].get("noun") == "resilience"
    assert any("resilient" in col for col in details["collocations"])

    # 4. Verify 10 distinct contextual examples
    assert len(examples) == 10
    for ex in examples:
        assert "resilient" in ex["example_text"].lower()

    # 5. Assert none of the old generic fallback strings exist
    assert "general meaning, usage, and definition" not in details["simple_meaning"].lower()
    assert "term related to" not in str(details["synonyms"]).lower()
    assert "concept of" not in str(details["synonyms"]).lower()
    assert "use 'resilient' in context" not in str(details["collocations"]).lower()
    for ex in examples:
        assert "applied to our current workflow" not in ex["example_text"]
        assert "used the word" not in ex["example_text"]


@pytest.mark.asyncio
async def test_stale_cached_content_is_upgraded_without_losing_user_state(client, auth_headers, db_session, test_user):
    """Ensure stale DB records are automatically upgraded while preserving user learning progress."""
    from models.vocabulary import Vocabulary, WordDetails, VocabularyExample

    # 1. Create a vocabulary record with advanced learning progress
    vocab = Vocabulary(
        user_id=test_user.id,
        word="resilient",
        status="practiced",
        mastery_score=0.75,
        practice_count=6,
        successful_usage_count=5,
        failed_recall_count=1,
    )
    db_session.add(vocab)
    db_session.commit()
    db_session.refresh(vocab)

    # 2. Inject stale generic records directly into DB (simulating data created before the fix)
    stale_details = WordDetails(
        vocabulary_id=vocab.id,
        simple_meaning="The general meaning, usage, and definition of the English term 'resilient'.",
        contextual_meaning="Used in everyday or professional communication when expressing concepts related to 'resilient'.",
        part_of_speech="word",
        pronunciation_text="/resilient/",
        synonyms=["term related to resilient", "concept of resilient"],
        antonyms=[],
        word_forms={"base": "resilient"},
        collocations=["use 'resilient' in context", "understand 'resilient'"],
        cefr_level="B1",
        difficulty_score=5.0,
    )
    stale_example = VocabularyExample(
        vocabulary_id=vocab.id,
        example_text="During the meeting, the manager mentioned how 'resilient' applied to our current workflow.",
        context_label="Workplace",
        order_index=0,
    )
    db_session.add(stale_details)
    db_session.add(stale_example)
    db_session.commit()

    # 3. Call learn endpoint
    learn_res = client.get(f"/api/v1/vocabulary/{vocab.id}/learn", headers=auth_headers)
    assert learn_res.status_code == 200
    data = learn_res.json()

    # 4. Assert user progress and learning state were completely preserved
    assert data["status"] == "practiced"
    assert data["mastery_score"] == 0.75
    assert data["practice_count"] == 6
    assert data["successful_usage_count"] == 5

    # 5. Assert stale content was replaced by real semantic content
    updated_details = data["details"]
    assert "withstand or recover quickly" in updated_details["simple_meaning"]
    assert updated_details["part_of_speech"] == "adjective"
    assert "ri-ZIL-yunt" in updated_details["pronunciation_text"]
    assert "general meaning, usage, and definition" not in updated_details["simple_meaning"]
    assert "term related to" not in str(updated_details["synonyms"])
    assert len(data["examples"]) == 10
    assert "applied to our current workflow" not in data["examples"][0]["example_text"]


@pytest.mark.asyncio
async def test_learn_content_lookup_by_word_and_id_and_repeated_calls(client, auth_headers):
    """Verify learn endpoint can be accessed by ID and by word, and repeated calls succeed without error."""
    # 1. Add word
    res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "resilient"})
    assert res.status_code == 201
    vocab_id = res.json()["id"]

    # 2. Access by UUID
    res_id = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
    assert res_id.status_code == 200
    assert res_id.json()["word"] == "resilient"
    assert len(res_id.json()["examples"]) == 10

    # 3. Access by word slug
    res_word = client.get("/api/v1/vocabulary/resilient/learn", headers=auth_headers)
    assert res_word.status_code == 200
    assert res_word.json()["id"] == vocab_id
    assert res_word.json()["details"]["simple_meaning"] == res_id.json()["details"]["simple_meaning"]

    # 4. Mark learned and re-fetch to ensure no regressions
    mark_res = client.post(f"/api/v1/vocabulary/{vocab_id}/mark-learned", headers=auth_headers)
    assert mark_res.status_code == 200
    assert mark_res.json()["status"] == "learned"

    # 5. Subsequent call returns learned status with identical upgraded content
    subsequent_res = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
    assert subsequent_res.status_code == 200
    assert subsequent_res.json()["status"] == "learned"
    assert len(subsequent_res.json()["examples"]) == 10




