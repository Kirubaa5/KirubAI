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
