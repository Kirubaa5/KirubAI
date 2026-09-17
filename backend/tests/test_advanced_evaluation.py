import pytest
from datetime import datetime, timezone
from ai.schemas import (
    DiagnosticErrorAI,
    EvaluationAI,
    MultiWordEvaluationAI,
    ConversationEvaluationAI,
)
from ai.mock_provider import MockLLMProvider, _analyze_text_diagnostics, _build_actionable_tips
from schemas.practice import DiagnosticErrorSchema
from models.vocabulary import Vocabulary
from models.practice import (
    PracticeSession,
    PracticeAttempt,
    MultiWordPracticeSession,
    MultiWordPracticeAttempt,
    ConversationSession,
    ConversationMessage,
)
from utils.security import create_access_token, hash_password
from models.user import User


# =============================================================================
# 1. Schema Validation Tests
# =============================================================================

def test_diagnostic_error_schema_validation():
    """Validate DiagnosticErrorAI and DiagnosticErrorSchema attributes."""
    err = DiagnosticErrorAI(
        error_type="collocation",
        original_text="discuss about the project",
        explanation="'Discuss' is transitive and does not take 'about'.",
        suggested_correction="discuss the project",
        severity="medium",
    )
    assert err.error_type == "collocation"
    assert err.original_text == "discuss about the project"
    assert err.suggested_correction == "discuss the project"
    assert err.severity == "medium"

    schema = DiagnosticErrorSchema(
        error_type="grammar",
        original_text="look forward to meet",
        explanation="Requires gerund.",
        suggested_correction="look forward to meeting",
        severity="high",
    )
    assert schema.error_type == "grammar"
    assert schema.severity == "high"


def test_evaluation_schemas_contain_diagnostics_and_cefr():
    """Verify EvaluationAI, MultiWordEvaluationAI, and ConversationEvaluationAI schemas."""
    err = DiagnosticErrorAI(
        error_type="spelling",
        original_text="hestitate",
        explanation="Misspelled.",
        suggested_correction="hesitate",
        severity="low",
    )

    eval_ai = EvaluationAI(
        vocabulary_usage_score=8.5,
        grammar_score=7.0,
        context_score=9.0,
        naturalness_score=8.0,
        overall_score=8.2,
        feedback="Good attempt with minor spelling error.",
        improved_version="I will not hesitate to proceed.",
        vocabulary_used_correctly=True,
        errors=[err],
        cefr_level="B1",
        actionable_tips=["Check spelling before finalizing."],
    )
    assert len(eval_ai.errors) == 1
    assert eval_ai.cefr_level == "B1"
    assert len(eval_ai.actionable_tips) == 1


# =============================================================================
# 2. Diagnostic Error Extraction Across All 5 Categories
# =============================================================================

def test_diagnostic_error_collocation_extraction():
    """Test extraction of collocation errors (discuss about, do a decision, make homework)."""
    text = "We need to discuss about this and do a decision before we make homework."
    errors = _analyze_text_diagnostics(text)
    types = [e.error_type for e in errors]
    assert "collocation" in types

    discuss_err = next(e for e in errors if "discuss about" in e.original_text.lower())
    assert discuss_err.suggested_correction == "discuss"
    assert discuss_err.error_type == "collocation"

    decision_err = next(e for e in errors if "decision" in e.original_text.lower())
    assert decision_err.suggested_correction == "make a decision"


def test_diagnostic_error_grammar_extraction():
    """Test extraction of grammar errors (look forward to meet, since 5 years, more better, to much)."""
    text = "I look forward to meet you since 5 years and it is more better but to much."
    errors = _analyze_text_diagnostics(text)
    types = [e.error_type for e in errors]
    assert "grammar" in types

    meet_err = next(e for e in errors if "look forward to" in e.original_text.lower())
    assert "meeting" in meet_err.suggested_correction

    since_err = next(e for e in errors if "since" in e.original_text.lower())
    assert "for 5 years" in since_err.suggested_correction

    comp_err = next(e for e in errors if "more better" in e.original_text.lower())
    assert comp_err.suggested_correction == "better"


def test_diagnostic_error_semantic_extraction():
    """Test extraction of semantic errors (effect as verb, loose as verb)."""
    text = "This unexpected change will effect our roadmap and we might loose our advantage."
    errors = _analyze_text_diagnostics(text)
    types = [e.error_type for e in errors]
    assert "semantic" in types

    effect_err = next(e for e in errors if "effect" in e.original_text.lower())
    assert effect_err.error_type == "semantic"
    assert effect_err.severity == "high"
    assert "affect" in effect_err.suggested_correction.lower()


def test_diagnostic_error_tone_extraction():
    """Test extraction of tone/register errors (gonna, wanna, hey guys)."""
    text = "Hey guys, I am gonna present our findings today."
    errors = _analyze_text_diagnostics(text)
    types = [e.error_type for e in errors]
    assert "tone" in types

    tone_err = next(e for e in errors if e.error_type == "tone")
    assert tone_err.severity == "low"


def test_diagnostic_error_spelling_extraction():
    """Test extraction of spelling errors (hestitate, vividely, hasle, perservere)."""
    text = "Please do not hestitate to reach out without any hasle, and perservere vividly."
    errors = _analyze_text_diagnostics(text)
    types = [e.error_type for e in errors]
    assert "spelling" in types

    spell_err = next(e for e in errors if "hestitate" in e.original_text.lower())
    assert spell_err.suggested_correction == "hesitate"


def test_clean_text_produces_empty_error_list():
    """Verify that natural, error-free input produces an empty error list."""
    clean_text = "I did not hesitate to share my perspective with the team during our quarterly review meeting."
    errors = _analyze_text_diagnostics(clean_text)
    assert errors == []
    tips = _build_actionable_tips(errors)
    assert len(tips) >= 2


# =============================================================================
# 3. Deterministic MockLLMProvider Evaluation
# =============================================================================

@pytest.mark.asyncio
async def test_mock_provider_evaluation_ai_with_errors():
    """Verify MockLLMProvider returns structured diagnostic errors and CEFR score."""
    provider = MockLLMProvider()
    prompt = """Evaluate the learner's response for the target English word "hesitate".

Scenario:
You are in a project meeting.

Learner's response:
"We should not hestitate to discuss about this issue."
"""
    result: EvaluationAI = await provider.generate_structured(
        prompt=prompt,
        response_schema=EvaluationAI,
    )
    assert isinstance(result, EvaluationAI)
    assert len(result.errors) >= 2
    err_types = {e.error_type for e in result.errors}
    assert "collocation" in err_types
    assert "spelling" in err_types
    assert result.cefr_level in ("B1", "A2")
    assert len(result.actionable_tips) > 0


@pytest.mark.asyncio
async def test_mock_provider_multi_word_evaluation_ai():
    """Verify MockLLMProvider produces diagnostic error analysis for multi-word synthesis."""
    provider = MockLLMProvider()
    prompt = """Evaluate the learner's multi-word response targeting: "hesitate", "vividly", "hassle".

Scenario:
Sprint coordination.

Learner's response:
"I look forward to meet the team and will not hesitate to handle this hassle vividly."
"""
    result: MultiWordEvaluationAI = await provider.generate_structured(
        prompt=prompt,
        response_schema=MultiWordEvaluationAI,
    )
    assert isinstance(result, MultiWordEvaluationAI)
    assert len(result.errors) >= 1
    assert result.errors[0].error_type == "grammar"
    assert result.cefr_level is not None
    assert len(result.actionable_tips) > 0


# =============================================================================
# 4. Persistence & API Integration Tests
# =============================================================================

def test_practice_attempt_persistence_and_retrieval(client, auth_headers, test_user, test_vocabulary, db_session):
    """Test scenario practice submit persists errors, cefr_level, and actionable_tips."""
    # 1. Start practice session
    start_res = client.post(
        "/api/v1/practice/start",
        json={"vocabulary_id": test_vocabulary.id},
        headers=auth_headers,
    )
    assert start_res.status_code == 201
    session_id = start_res.json()["session_id"]

    # 2. Submit attempt with a deliberate error
    submit_res = client.post(
        f"/api/v1/practice/{session_id}/submit",
        json={
            "scenario_text": "In a team meeting, discuss the roadmap.",
            "response": "I did not hesitate to discuss about our project strategy.",
        },
        headers=auth_headers,
    )
    assert submit_res.status_code == 200
    data = submit_res.json()
    assert "errors" in data
    assert len(data["errors"]) >= 1
    assert data["errors"][0]["error_type"] == "collocation"
    assert data["errors"][0]["original_text"] == "discuss about"
    assert data["cefr_level"] is not None
    assert "actionable_tips" in data
    assert len(data["actionable_tips"]) > 0

    # 3. Retrieve session details and verify persisted attempt
    get_res = client.get(
        f"/api/v1/practice/{session_id}",
        headers=auth_headers,
    )
    assert get_res.status_code == 200
    session_data = get_res.json()
    assert len(session_data["attempts"]) == 1
    persisted_att = session_data["attempts"][0]
    assert len(persisted_att["errors"]) >= 1
    assert persisted_att["cefr_level"] is not None


def test_multi_word_practice_persistence_and_retrieval(client, auth_headers, test_user, db_session):
    """Test multi-word practice submit persists errors, cefr_level, and actionable_tips."""
    # Seed 3 practiced vocabulary words
    for w in ["hesitate", "vividly", "hassle"]:
        v = Vocabulary(
            user_id=test_user.id,
            word=w,
            status="practiced",
            mastery_score=0.4,
        )
        db_session.add(v)
    db_session.commit()

    # Start multi-word session
    start_res = client.post(
        "/api/v1/practice/multi-word",
        json={},
        headers=auth_headers,
    )
    assert start_res.status_code == 201
    session_id = start_res.json()["session_id"]

    # Submit multi-word response with intentional error
    submit_res = client.post(
        f"/api/v1/practice/multi-word/{session_id}/submit",
        json={
            "response": "We will not hestitate to solve the hassle and remember our achievements vividly.",
        },
        headers=auth_headers,
    )
    assert submit_res.status_code == 200
    data = submit_res.json()
    assert "errors" in data
    assert len(data["errors"]) >= 1
    assert data["errors"][0]["error_type"] == "spelling"
    assert data["cefr_level"] is not None
    assert len(data["actionable_tips"]) > 0


def test_conversation_evaluation_persistence_and_retrieval(client, auth_headers, test_user, db_session):
    """Test conversation end persists structured errors, cefr_level, and actionable_tips."""
    # Start conversation
    start_res = client.post(
        "/api/v1/conversations/start",
        json={"topic": "Career Planning", "use_vocabulary": False, "target_words": ["hesitate"]},
        headers=auth_headers,
    )
    assert start_res.status_code == 201
    session_id = start_res.json()["session_id"]

    # Send message with intentional grammar error
    msg_res = client.post(
        f"/api/v1/conversations/{session_id}/message",
        json={"content": "I look forward to meet my manager and I do not hesitate to ask questions."},
        headers=auth_headers,
    )
    assert msg_res.status_code == 200

    # End conversation
    end_res = client.post(
        f"/api/v1/conversations/{session_id}/end",
        headers=auth_headers,
    )
    assert end_res.status_code == 200
    eval_data = end_res.json()["evaluation"]
    assert "errors" in eval_data
    assert len(eval_data["errors"]) >= 1
    assert eval_data["errors"][0]["error_type"] == "grammar"
    assert eval_data["cefr_level"] is not None
    assert "actionable_tips" in eval_data


# =============================================================================
# 5. User Isolation & Backward Compatibility
# =============================================================================

def test_user_isolation_practice_diagnostics(client, db_session, test_user, test_vocabulary):
    """Verify User B cannot access User A's practice diagnostics."""
    # Create User B
    user_b = User(
        email="user_b@example.com",
        full_name="User B",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    token_b = create_access_token({"sub": user_b.id, "email": user_b.email})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A starts session
    token_a = create_access_token({"sub": test_user.id, "email": test_user.email})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    start_res = client.post(
        "/api/v1/practice/start",
        json={"vocabulary_id": test_vocabulary.id},
        headers=headers_a,
    )
    session_id = start_res.json()["session_id"]

    # User B attempts to access User A's session
    get_res = client.get(
        f"/api/v1/practice/{session_id}",
        headers=headers_b,
    )
    assert get_res.status_code == 404


def test_backward_compatibility_null_errors_handling(client, auth_headers, test_user, test_vocabulary, db_session):
    """Verify that legacy attempts with null/empty error columns are handled safely."""
    session = PracticeSession(
        user_id=test_user.id,
        vocabulary_id=test_vocabulary.id,
        session_type="scenario",
        status="active",
    )
    db_session.add(session)
    db_session.flush()

    # Legacy attempt with null errors
    legacy_attempt = PracticeAttempt(
        session_id=session.id,
        vocabulary_id=test_vocabulary.id,
        scenario_text="Legacy scenario text",
        user_response="I hesitated before answering.",
        vocabulary_usage_score=9.0,
        grammar_score=8.5,
        context_score=9.0,
        naturalness_score=8.5,
        overall_score=8.7,
        feedback="Great job.",
        improved_version=None,
        is_successful=True,
        errors=None,
        cefr_level=None,
        actionable_tips=None,
    )
    db_session.add(legacy_attempt)
    db_session.commit()

    # Fetch session via API
    res = client.get(f"/api/v1/practice/{session.id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["attempts"]) == 1
    att = data["attempts"][0]
    assert att["errors"] == []
    assert att["cefr_level"] == "B1"
    assert att["actionable_tips"] == []
