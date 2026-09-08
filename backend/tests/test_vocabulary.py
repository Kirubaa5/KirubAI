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

    response = client.get(f"/api/v1/vocabulary/{vocab_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["word"] == "resilient"


def test_delete_vocabulary(client, auth_headers):
    create_res = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "ephemeral"})
    vocab_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/vocabulary/{vocab_id}", headers=auth_headers)
    assert del_res.status_code == 204

    get_res = client.get(f"/api/v1/vocabulary/{vocab_id}", headers=auth_headers)
    assert get_res.status_code == 404
