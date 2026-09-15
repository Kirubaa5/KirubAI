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
    """Ensure unknown words return clean, grammatically safe structures without fabricated synonyms."""
    res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "unprecedentedly"})
    assert res.status_code == 201
    vocab_id = res.json()["id"]

    learn = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers).json()
    details = learn["details"]

    # Suffix inference should identify adverb
    assert details["part_of_speech"] == "adverb"

    # No fabricated phrases
    assert "term related to" not in str(details["synonyms"])
    assert "concept of" not in str(details["synonyms"])
    assert details["synonyms"] == []
    assert details["antonyms"] == []

    # Safe word forms without fake suffixes like 'unprecedentedlytion'
    assert "unprecedentedlytion" not in str(details["word_forms"])
    assert details["word_forms"] == {"base": "unprecedentedly"}


