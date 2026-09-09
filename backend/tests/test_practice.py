import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models.vocabulary import Vocabulary
from models.practice import PracticeSession, PracticeAttempt


def test_start_practice_session_success(client: TestClient, auth_headers: dict, test_vocabulary: Vocabulary):
    response = client.post(
        "/api/v1/practice/start",
        headers=auth_headers,
        json={"vocabulary_id": test_vocabulary.id, "session_type": "scenario"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["vocabulary_id"] == test_vocabulary.id
    assert data["target_word"] == test_vocabulary.word
    assert "scenario" in data
    assert "situation" in data["scenario"]
    assert "prompt" in data["scenario"]
    assert len(data["scenario"]["situation"]) > 0


def test_start_practice_session_not_found(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/v1/practice/start",
        headers=auth_headers,
        json={"vocabulary_id": "non-existent-vocab-id", "session_type": "scenario"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Vocabulary word not found"


def test_generate_new_scenario(client: TestClient, auth_headers: dict, test_vocabulary: Vocabulary):
    # Start session first
    start_resp = client.post(
        "/api/v1/practice/start",
        headers=auth_headers,
        json={"vocabulary_id": test_vocabulary.id},
    )
    session_id = start_resp.json()["session_id"]

    # Generate new scenario
    scen_resp = client.post(
        f"/api/v1/practice/{session_id}/scenario",
        headers=auth_headers,
    )
    assert scen_resp.status_code == 200
    scen_data = scen_resp.json()
    assert "situation" in scen_data
    assert "prompt" in scen_data


def test_submit_practice_attempt_successful(
    client: TestClient,
    auth_headers: dict,
    test_vocabulary: Vocabulary,
    db_session: Session,
):
    # Start session
    start_resp = client.post(
        "/api/v1/practice/start",
        headers=auth_headers,
        json={"vocabulary_id": test_vocabulary.id},
    )
    session_id = start_resp.json()["session_id"]
    scenario_text = start_resp.json()["scenario"]["situation"]

    # Submit valid attempt with target word
    submit_resp = client.post(
        f"/api/v1/practice/{session_id}/submit",
        headers=auth_headers,
        json={
            "scenario_text": scenario_text,
            "response": f"I would hesitate to commit to that deadline because my schedule is already full.",
        },
    )
    assert submit_resp.status_code == 200
    data = submit_resp.json()

    assert data["session_id"] == session_id
    assert data["target_word"] == test_vocabulary.word
    assert data["is_successful"] is True
    assert data["scores"]["vocabulary_usage"] >= 5.0
    assert data["scores"]["overall"] >= 6.0
    assert data["scores"]["grammar"] > 0
    assert data["scores"]["context"] > 0
    assert data["scores"]["naturalness"] > 0
    assert len(data["feedback"]) > 0
    assert len(data["improved_version"]) > 0

    # Verify DB updates on vocabulary
    db_session.refresh(test_vocabulary)
    assert test_vocabulary.status == "practiced"
    assert test_vocabulary.practice_count == 1
    assert test_vocabulary.successful_usage_count == 1
    assert test_vocabulary.mastery_score > 0.0
    assert test_vocabulary.last_practiced_at is not None


def test_submit_practice_attempt_unsuccessful(
    client: TestClient,
    auth_headers: dict,
    test_vocabulary: Vocabulary,
    db_session: Session,
):
    # Start session
    start_resp = client.post(
        "/api/v1/practice/start",
        headers=auth_headers,
        json={"vocabulary_id": test_vocabulary.id},
    )
    session_id = start_resp.json()["session_id"]
    scenario_text = start_resp.json()["scenario"]["situation"]

    # Submit attempt without target word
    submit_resp = client.post(
        f"/api/v1/practice/{session_id}/submit",
        headers=auth_headers,
        json={
            "scenario_text": scenario_text,
            "response": "Sure, I can do that for you right away tomorrow morning without problem.",
        },
    )
    assert submit_resp.status_code == 200
    data = submit_resp.json()

    assert data["is_successful"] is False
    assert data["scores"]["vocabulary_usage"] < 5.0
    assert "feedback" in data


def test_get_practice_session_details(
    client: TestClient,
    auth_headers: dict,
    test_vocabulary: Vocabulary,
):
    # Start session and make attempt
    start_resp = client.post(
        "/api/v1/practice/start",
        headers=auth_headers,
        json={"vocabulary_id": test_vocabulary.id},
    )
    session_id = start_resp.json()["session_id"]
    scenario_text = start_resp.json()["scenario"]["situation"]

    client.post(
        f"/api/v1/practice/{session_id}/submit",
        headers=auth_headers,
        json={
            "scenario_text": scenario_text,
            "response": f"I hesitate to agree without checking my calendar first.",
        },
    )

    # Get session details
    get_resp = client.get(
        f"/api/v1/practice/{session_id}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == session_id
    assert data["total_attempts"] == 1
    assert data["successful_attempts"] == 1
    assert data["average_score"] is not None
    assert len(data["attempts"]) == 1
    assert data["attempts"][0]["scenario_text"] == scenario_text


def test_list_practice_sessions(
    client: TestClient,
    auth_headers: dict,
    test_vocabulary: Vocabulary,
):
    # Create 2 sessions
    client.post(
        "/api/v1/practice/start",
        headers=auth_headers,
        json={"vocabulary_id": test_vocabulary.id},
    )
    client.post(
        "/api/v1/practice/start",
        headers=auth_headers,
        json={"vocabulary_id": test_vocabulary.id},
    )

    response = client.get("/api/v1/practice/sessions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    assert data["page"] == 1


def test_complete_practice_session(
    client: TestClient,
    auth_headers: dict,
    test_vocabulary: Vocabulary,
):
    start_resp = client.post(
        "/api/v1/practice/start",
        headers=auth_headers,
        json={"vocabulary_id": test_vocabulary.id},
    )
    session_id = start_resp.json()["session_id"]

    # Complete session
    comp_resp = client.post(
        f"/api/v1/practice/{session_id}/complete",
        headers=auth_headers,
    )
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "completed"
    assert comp_resp.json()["completed_at"] is not None

    # Submitting to completed session should fail
    fail_submit = client.post(
        f"/api/v1/practice/{session_id}/submit",
        headers=auth_headers,
        json={
            "scenario_text": "Some situation",
            "response": "I hesitate to reply.",
        },
    )
    assert fail_submit.status_code == 400
    assert "completed" in fail_submit.json()["detail"].lower()


def test_practice_unauthorized(client: TestClient, test_vocabulary: Vocabulary):
    response = client.post(
        "/api/v1/practice/start",
        json={"vocabulary_id": test_vocabulary.id},
    )
    assert response.status_code == 401
