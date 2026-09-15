def test_add_vocabulary_success(client, auth_headers):
    response = client.post(
        "/api/v1/vocabulary",
        headers=auth_headers,
        json={"word": "hesitate"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["word"] == "hesitate"
    assert data["status"] == "new"
    assert data["mastery_score"] == 0.0


def test_add_vocabulary_duplicate(client, auth_headers):
    # Add first time
    client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "hesitate"})
    # Add second time
    response = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "hesitate"})
    assert response.status_code == 409
    assert "already in your vocabulary" in response.json()["detail"]


def test_list_vocabulary_pagination(client, auth_headers):
    # Add 3 words
    words = ["hesitate", "confident", "perseverance"]
    for w in words:
        client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": w})

    response = client.get("/api/v1/vocabulary?page=1&per_page=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["pages"] == 2


def test_list_vocabulary_search(client, auth_headers):
    words = ["hesitate", "confident", "perseverance"]
    for w in words:
        client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": w})

    response = client.get("/api/v1/vocabulary?search=conf", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["word"] == "confident"


def test_get_vocabulary_detail(client, auth_headers):
    create_res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "resilient"})
    vocab_id = create_res.json()["id"]

    # Access by ID
    response = client.get(f"/api/v1/vocabulary/{vocab_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["word"] == "resilient"

    # Access by word slug
    response_slug = client.get("/api/v1/vocabulary/resilient", headers=auth_headers)
    assert response_slug.status_code == 200
    assert response_slug.json()["id"] == vocab_id
    assert response_slug.json()["word"] == "resilient"


def test_delete_vocabulary(client, auth_headers):
    create_res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "ephemeral"})
    vocab_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/vocabulary/{vocab_id}", headers=auth_headers)
    assert del_res.status_code == 204

    get_res = client.get(f"/api/v1/vocabulary/{vocab_id}", headers=auth_headers)
    assert get_res.status_code == 404


def test_list_vocabulary_with_null_collection_details(client, auth_headers, test_user, db_session):
    """Regression test: vocabulary list with partially null word_details serializes cleanly."""
    from models.vocabulary import Vocabulary, WordDetails

    # Create word directly in DB with null collection fields on WordDetails
    vocab = Vocabulary(
        user_id=test_user.id,
        word="ubiquitous",
        status="new",
        mastery_score=0.0,
    )
    db_session.add(vocab)
    db_session.commit()
    db_session.refresh(vocab)

    details = WordDetails(
        vocabulary_id=vocab.id,
        simple_meaning="Present, appearing, or found everywhere.",
        synonyms=None,
        antonyms=None,
        word_forms=None,
        collocations=None,
    )
    db_session.add(details)
    db_session.commit()

    # List endpoint must succeed and return defaults for null collections
    res = client.get("/api/v1/vocabulary?search=ubiquitous", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["word"] == "ubiquitous"
    assert item["details"]["synonyms"] == []
    assert item["details"]["antonyms"] == []
    assert item["details"]["word_forms"] == {}
    assert item["details"]["collocations"] == []

