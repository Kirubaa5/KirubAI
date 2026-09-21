import pytest
from fastapi.testclient import TestClient
from database import get_db
from models.user import User
from models.vocabulary import Vocabulary
from utils.security import hash_password, create_access_token
from config import _normalize_database_url, Settings


class TestSecurityAndHardening:
    def test_database_url_normalization(self):
        """Ensure postgres:// is automatically normalized to postgresql://."""
        raw_supabase_url = "postgres://postgres.abc:password123@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        normalized = _normalize_database_url(raw_supabase_url)
        assert normalized.startswith("postgresql://")
        assert "postgres.abc:password123" in normalized

        standard_url = "postgresql://user:pass@localhost:5432/db"
        assert _normalize_database_url(standard_url) == standard_url

    def test_cors_origins_validator(self):
        """Ensure CORS_ORIGINS parses comma-separated strings."""
        s = Settings(
            CORS_ORIGINS="https://kirubai.vercel.app, http://localhost:5173",
            _env_file=None,
        )
        assert "https://kirubai.vercel.app" in s.CORS_ORIGINS
        assert "http://localhost:5173" in s.CORS_ORIGINS
        assert len(s.CORS_ORIGINS) == 2

    def test_security_headers_present(self, client: TestClient):
        """Verify all responses include standard security headers."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_health_check_endpoint(self, client: TestClient):
        """Health check returns 200 with application status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data

    def test_unauthenticated_access_rejected(self, client: TestClient):
        """Protected endpoints reject requests without token."""
        response = client.get("/api/v1/vocabulary")
        assert response.status_code == 401
        assert "Authentication credentials required" in response.json()["detail"]

    def test_invalid_token_rejected(self, client: TestClient):
        """Invalid JWT tokens return 401."""
        response = client.get(
            "/api/v1/vocabulary",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert response.status_code == 401
        assert "Invalid or expired" in response.json()["detail"]

    def test_user_data_isolation(self, client: TestClient, db_session, test_user):
        """User B cannot access or modify User A's vocabulary."""
        # Create User A's word
        vocab_a = Vocabulary(
            user_id=test_user.id,
            word="serendipity",
            status="new",
        )
        db_session.add(vocab_a)
        db_session.commit()
        db_session.refresh(vocab_a)

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

        # User B lists vocabulary — should be empty
        res_list = client.get("/api/v1/vocabulary", headers=headers_b)
        assert res_list.status_code == 200
        assert res_list.json()["total"] == 0

        # User B attempts to access User A's word
        res_get = client.get(f"/api/v1/vocabulary/{vocab_a.id}", headers=headers_b)
        assert res_get.status_code == 404

        # User B attempts to delete User A's word
        res_delete = client.delete(f"/api/v1/vocabulary/{vocab_a.id}", headers=headers_b)
        assert res_delete.status_code == 404

        # Verify User A's word is untouched
        token_a = create_access_token({"sub": test_user.id, "email": test_user.email})
        res_check = client.get(
            f"/api/v1/vocabulary/{vocab_a.id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res_check.status_code == 200
        assert res_check.json()["word"] == "serendipity"
