import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from app.main import app, get_session
from app.models import User

# ---- test DB wiring ----
@pytest.fixture
def test_client():
    # Use StaticPool so the in-memory SQLite database persists across connections
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def register(client, email="alice@example.com", password="supersecret"):
    return client.post("/auth/register", json={"email": email, "password": password})

def login(client, email="alice@example.com", password="supersecret"):
    return client.post("/auth/login", data={"username": email, "password": password})

# ---- unit-ish test of data layer behavior via API ----
class TestAuth:
    def test_register_success(self, test_client):
        r = register(test_client)
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "alice@example.com"
        assert "id" in body

    def test_register_duplicate_email(self, test_client):
        r1 = register(test_client)
        assert r1.status_code == 201
        r2 = register(test_client)
        assert r2.status_code == 409

    def test_register_weak_password(self, test_client):
        r = register(test_client, password="short")
        assert r.status_code == 400

    def test_login_success_and_me(self, test_client):
        register(test_client)
        r = login(test_client)
        assert r.status_code == 200
        token = r.json()["access_token"]
        me = test_client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "alice@example.com"

    def test_login_bad_password(self, test_client):
        register(test_client)
        r = login(test_client, password="wrong")
        assert r.status_code == 401

    def test_me_requires_auth(self, test_client):
        r = test_client.get("/me")
        assert r.status_code == 401


class TestAuthExtended:
    def test_register_invalid_email(self, test_client):
        r = test_client.post("/auth/register", json={"email": "not-an-email", "password": "supersecret"})
        assert r.status_code == 422

    def test_register_missing_password(self, test_client):
        r = test_client.post("/auth/register", json={"email": "bob@example.com"})
        assert r.status_code == 422

    def test_register_missing_email(self, test_client):
        r = test_client.post("/auth/register", json={"password": "supersecret"})
        assert r.status_code == 422

    def test_login_nonexistent_user(self, test_client):
        r = test_client.post("/auth/login", data={"username": "nouser@example.com", "password": "whateverpass"})
        assert r.status_code == 401

    def test_token_response_shape(self, test_client):
        # register and login
        reg = test_client.post("/auth/register", json={"email": "carol@example.com", "password": "supersecret"})
        assert reg.status_code == 201
        login = test_client.post("/auth/login", data={"username": "carol@example.com", "password": "supersecret"})
        assert login.status_code == 200
        body = login.json()
        assert isinstance(body.get("access_token"), str) and body["access_token"]
        assert body.get("token_type") == "bearer"

    def test_me_with_invalid_token(self, test_client):
        r = test_client.get("/me", headers={"Authorization": "Bearer invalid.token.value"})
        assert r.status_code == 401
