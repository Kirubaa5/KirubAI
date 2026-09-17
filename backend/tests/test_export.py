import json
import io
import csv
from datetime import datetime, timezone, timedelta
import pytest

from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.user import User
from utils.security import hash_password, create_access_token


@pytest.fixture
def rich_vocabulary_set(db_session, test_user):
    """Seed user vocabulary with various statuses, CEFR levels, and learning states."""
    now = datetime.now(timezone.utc)

    # 1. Word: hesitate (struggling, B1, due for review)
    v1 = Vocabulary(
        user_id=test_user.id,
        word="hesitate",
        status="struggling",
        mastery_score=0.25,
        practice_count=4,
        successful_usage_count=1,
        failed_recall_count=3,
        review_interval_days=1,
        next_review_at=now - timedelta(days=1),  # Due!
        last_practiced_at=now - timedelta(days=2),
        last_reviewed_at=now - timedelta(days=1),
        created_at=now - timedelta(days=10),
    )
    db_session.add(v1)
    db_session.commit()
    db_session.refresh(v1)

    d1 = WordDetails(
        vocabulary_id=v1.id,
        simple_meaning="To pause before saying or doing something.",
        contextual_meaning="Hesitate is often used in professional communication to invite questions politely.",
        part_of_speech="verb",
        pronunciation_text="/ˈhez.ɪ.teɪt/",
        cefr_level="B1",
        difficulty_score=0.35,
        synonyms=["pause", "waver", "delay"],
        antonyms=["proceed", "advance"],
        word_forms={"verb": "hesitate", "noun": "hesitation", "adjective": "hesitant", "adverb": "hesitantly"},
        collocations=["hesitate to ask", "without hesitation", "hesitate a moment"],
    )
    db_session.add(d1)

    e1 = VocabularyExample(
        vocabulary_id=v1.id,
        example_text="Don't hesitate to reach out if you encounter any technical issues.",
        context_label="Workplace",
        order_index=1,
    )
    e2 = VocabularyExample(
        vocabulary_id=v1.id,
        example_text="She hesitated for a second before accepting the job offer.",
        context_label="Casual",
        order_index=2,
    )
    db_session.add_all([e1, e2])

    # 2. Word: resilient (mastered, B2, not due)
    v2 = Vocabulary(
        user_id=test_user.id,
        word="resilient",
        status="mastered",
        mastery_score=0.92,
        practice_count=6,
        successful_usage_count=6,
        failed_recall_count=0,
        review_interval_days=30,
        next_review_at=now + timedelta(days=20),  # Not due
        last_practiced_at=now - timedelta(days=5),
        last_reviewed_at=now - timedelta(days=1),
        created_at=now - timedelta(days=30),
    )
    db_session.add(v2)
    db_session.commit()
    db_session.refresh(v2)

    d2 = WordDetails(
        vocabulary_id=v2.id,
        simple_meaning="Able to recover quickly from difficult conditions.",
        contextual_meaning="Used to describe resilient systems, teams, or individuals.",
        part_of_speech="adjective",
        pronunciation_text="/rɪˈzɪl.jənt/",
        cefr_level="B2",
        difficulty_score=0.6,
        synonyms=["tough", "flexible", "adaptable"],
        antonyms=["fragile", "vulnerable"],
        word_forms={"adjective": "resilient", "noun": "resilience", "adverb": "resiliently"},
        collocations=["highly resilient", "resilient infrastructure", "remain resilient"],
    )
    db_session.add(d2)

    e3 = VocabularyExample(
        vocabulary_id=v2.id,
        example_text="The startup built a remarkably resilient cloud infrastructure.",
        context_label="Technical",
        order_index=1,
    )
    db_session.add(e3)

    # 3. Word: eloquent (active/practiced, C1, not due)
    v3 = Vocabulary(
        user_id=test_user.id,
        word="eloquent",
        status="practiced",
        mastery_score=0.60,
        practice_count=2,
        successful_usage_count=2,
        failed_recall_count=0,
        review_interval_days=7,
        next_review_at=now + timedelta(days=5),
        created_at=now - timedelta(days=5),
    )
    db_session.add(v3)
    db_session.commit()
    db_session.refresh(v3)

    d3 = WordDetails(
        vocabulary_id=v3.id,
        simple_meaning="Fluent or persuasive in speaking or writing.",
        contextual_meaning="Expressing ideas clearly and with graceful style.",
        part_of_speech="adjective",
        pronunciation_text="/ˈel.ə.kwənt/",
        cefr_level="C1",
        difficulty_score=0.75,
        synonyms=["articulate", "expressive", "fluent"],
        antonyms=["inarticulate"],
        word_forms={"adjective": "eloquent", "noun": "eloquence", "adverb": "eloquently"},
        collocations=["eloquent speech", "eloquent defense"],
    )
    db_session.add(d3)

    # 4. Word: nascent (new, no details yet)
    v4 = Vocabulary(
        user_id=test_user.id,
        word="nascent",
        status="new",
        mastery_score=0.0,
        practice_count=0,
        successful_usage_count=0,
        failed_recall_count=0,
        review_interval_days=1,
        created_at=now - timedelta(days=1),
    )
    db_session.add(v4)
    db_session.commit()

    return [v1, v2, v3, v4]


def test_export_preview_summary(client, auth_headers, rich_vocabulary_set):
    """Test preview endpoint returns aggregated stats and matching counts."""
    response = client.get("/api/v1/export/preview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_vocabulary_count"] == 4
    assert data["matching_words_count"] == 4
    assert "struggling" in data["status_distribution"]
    assert "mastered" in data["status_distribution"]
    assert "practiced" in data["status_distribution"]
    assert "new" in data["status_distribution"]
    assert "B1" in data["cefr_distribution"]
    assert "B2" in data["cefr_distribution"]
    assert "C1" in data["cefr_distribution"]
    assert "eloquent" in data["sample_words"]


def test_export_csv_generation(client, auth_headers, rich_vocabulary_set):
    """Test CSV export generates correct columns, headers, and BOM encoded UTF-8."""
    response = client.get("/api/v1/export/csv", headers=auth_headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment; filename=" in response.headers["content-disposition"]

    # Decode using utf-8-sig to verify BOM and content
    content_str = response.content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(content_str))
    rows = list(reader)

    # Header check
    headers = rows[0]
    assert headers[0] == "Word"
    assert headers[1] == "Part of Speech"
    assert headers[2] == "CEFR Level"
    assert headers[3] == "Simple Meaning"
    assert headers[10] == "Examples"
    assert headers[11] == "Status"
    assert headers[12] == "Mastery Score"

    # 4 data rows + 1 header row = 5 rows
    assert len(rows) == 5

    # Check that hesitate row has examples and collocations
    hesitate_row = next(r for r in rows[1:] if r[0] == "hesitate")
    assert hesitate_row[1] == "verb"
    assert hesitate_row[2] == "B1"
    assert "hesitate to ask" in hesitate_row[9]  # collocations
    assert "Workplace" in hesitate_row[10]  # examples

    # Check that nascent row (missing details) does not crash and renders empty/defaults
    nascent_row = next(r for r in rows[1:] if r[0] == "nascent")
    assert nascent_row[1] == ""  # POS empty
    assert nascent_row[3] == ""  # Simple meaning empty
    assert nascent_row[11] == "new"  # status


def test_export_anki_tsv_generation(client, auth_headers, rich_vocabulary_set):
    """Test Anki TSV format with standard directives and HTML card layouts."""
    response = client.get("/api/v1/export/anki?format_type=tsv", headers=auth_headers)
    assert response.status_code == 200
    assert "text/tab-separated-values" in response.headers["content-type"]

    content = response.content.decode("utf-8")
    lines = [l for l in content.split("\n") if l.strip()]

    # Header directives
    assert lines[0] == "#separator:tab"
    assert lines[1] == "#html:true"
    assert lines[2] == "#tags column:6"

    # Card rows (4 items)
    card_lines = lines[3:]
    assert len(card_lines) == 4

    # Check resilient card line
    resilient_line = next(l for l in card_lines if "resilient" in l)
    fields = resilient_line.split("\t")
    assert len(fields) == 6

    front = fields[0]
    back = fields[1]
    pos = fields[2]
    cefr = fields[3]
    mastery = fields[4]
    tags = fields[5]

    assert "resilient" in front
    assert "Meaning:" in back
    assert "Forms:" in back
    assert "Collocations:" in back
    assert "B2" in cefr
    assert "KirubAI CEFR_B2 Status_mastered" in tags


def test_export_anki_csv_generation(client, auth_headers, rich_vocabulary_set):
    """Test Anki CSV format option."""
    response = client.get("/api/v1/export/anki?format_type=csv", headers=auth_headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

    content = response.content.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert rows[0] == ["Front", "Back", "Part of Speech", "CEFR Level", "Status", "Tags"]
    assert len(rows) == 5


def test_export_json_generation(client, auth_headers, rich_vocabulary_set):
    """Test full JSON export archive."""
    response = client.get("/api/v1/export/json?download=true", headers=auth_headers)
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "attachment; filename=" in response.headers["content-disposition"]

    data = response.json()
    assert data["app"] == "KirubAI"
    assert data["version"] == "0.1.0"
    assert data["total_words"] == 4
    assert len(data["vocabulary"]) == 4

    hesitate_item = next(item for item in data["vocabulary"] if item["word"] == "hesitate")
    assert hesitate_item["status"] == "struggling"
    assert hesitate_item["mastery_score"] == 0.25
    assert hesitate_item["details"]["cefr_level"] == "B1"
    assert len(hesitate_item["examples"]) == 2
    assert hesitate_item["details"]["word_forms"]["noun"] == "hesitation"


def test_export_filters_status_and_cefr(client, auth_headers, rich_vocabulary_set):
    """Test filtering by status (active, mastered, struggling, due) and CEFR level."""
    # Filter: mastered only -> 1 word (resilient)
    res_mastered = client.get("/api/v1/export/json?status=mastered&download=false", headers=auth_headers)
    assert res_mastered.status_code == 200
    assert res_mastered.json()["total_words"] == 1
    assert res_mastered.json()["vocabulary"][0]["word"] == "resilient"

    # Filter: struggling only -> 1 word (hesitate)
    res_struggling = client.get("/api/v1/export/json?status=struggling&download=false", headers=auth_headers)
    assert res_struggling.status_code == 200
    assert res_struggling.json()["total_words"] == 1
    assert res_struggling.json()["vocabulary"][0]["word"] == "hesitate"

    # Filter: due for review -> 1 word (hesitate)
    res_due = client.get("/api/v1/export/json?status=due&download=false", headers=auth_headers)
    assert res_due.status_code == 200
    assert res_due.json()["total_words"] == 1
    assert res_due.json()["vocabulary"][0]["word"] == "hesitate"

    # Filter: active -> practiced, recalled, reinforced, learned -> 1 word (eloquent)
    res_active = client.get("/api/v1/export/json?status=active&download=false", headers=auth_headers)
    assert res_active.status_code == 200
    assert res_active.json()["total_words"] == 1
    assert res_active.json()["vocabulary"][0]["word"] == "eloquent"

    # Filter: CEFR level B2 -> resilient
    res_cefr = client.get("/api/v1/export/json?cefr_level=B2&download=false", headers=auth_headers)
    assert res_cefr.status_code == 200
    assert res_cefr.json()["total_words"] == 1
    assert res_cefr.json()["vocabulary"][0]["word"] == "resilient"

    # Filter: CEFR level C1 -> eloquent
    res_c1 = client.get("/api/v1/export/json?cefr_level=C1&download=false", headers=auth_headers)
    assert res_c1.status_code == 200
    assert res_c1.json()["total_words"] == 1
    assert res_c1.json()["vocabulary"][0]["word"] == "eloquent"


def test_export_filters_mastery_range(client, auth_headers, rich_vocabulary_set):
    """Test filtering by min and max mastery score."""
    # min_mastery=0.5 -> resilient (0.92) and eloquent (0.60)
    res = client.get("/api/v1/export/json?min_mastery=0.5&download=false", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total_words"] == 2
    words = [w["word"] for w in res.json()["vocabulary"]]
    assert "resilient" in words
    assert "eloquent" in words


def test_export_empty_dataset(client, auth_headers):
    """Test exporting when user has zero words."""
    res_csv = client.get("/api/v1/export/csv", headers=auth_headers)
    assert res_csv.status_code == 200
    content = res_csv.content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    # Header row only
    assert len(rows) == 1

    res_preview = client.get("/api/v1/export/preview", headers=auth_headers)
    assert res_preview.status_code == 200
    assert res_preview.json()["total_vocabulary_count"] == 0
    assert res_preview.json()["matching_words_count"] == 0

    res_json = client.get("/api/v1/export/json?download=false", headers=auth_headers)
    assert res_json.status_code == 200
    assert res_json.json()["total_words"] == 0


def test_export_user_isolation(client, auth_headers, db_session, rich_vocabulary_set):
    """Test that User B cannot see or export User A's vocabulary."""
    # Create User B
    user_b = User(
        email="user_b@example.com",
        full_name="User B",
        hashed_password=hash_password("password123"),
        english_level="intermediate",
        daily_goal=5,
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    # Add 1 word for User B
    v_b = Vocabulary(
        user_id=user_b.id,
        word="serendipity",
        status="new",
        mastery_score=0.0,
    )
    db_session.add(v_b)
    db_session.commit()

    token_b = create_access_token({"sub": user_b.id, "email": user_b.email})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B exports JSON
    res_b = client.get("/api/v1/export/json?download=false", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["total_words"] == 1
    assert data_b["vocabulary"][0]["word"] == "serendipity"
    # Ensure User B does NOT see User A's words
    words_b = [w["word"] for w in data_b["vocabulary"]]
    assert "hesitate" not in words_b
    assert "resilient" not in words_b


def test_export_unauthorized_access(client):
    """Test that unauthenticated requests to export endpoints return 401."""
    res_csv = client.get("/api/v1/export/csv")
    assert res_csv.status_code == 401

    res_anki = client.get("/api/v1/export/anki")
    assert res_anki.status_code == 401

    res_json = client.get("/api/v1/export/json")
    assert res_json.status_code == 401

    res_preview = client.get("/api/v1/export/preview")
    assert res_preview.status_code == 401


def test_unified_export_endpoint(client, auth_headers, rich_vocabulary_set):
    """Test the unified /api/v1/export endpoint with format parameter."""
    res_csv = client.get("/api/v1/export?format=csv", headers=auth_headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]

    res_anki = client.get("/api/v1/export?format=anki", headers=auth_headers)
    assert res_anki.status_code == 200
    assert "text/tab-separated-values" in res_anki.headers["content-type"]

    res_json = client.get("/api/v1/export?format=json", headers=auth_headers)
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]
