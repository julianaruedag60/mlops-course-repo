import pytest
from fastapi.testclient import TestClient

from app import app, get_model


class FakeModel:
    """Modelo falso: devuelve un valor fijo y registra las llamadas."""

    def __init__(self) -> None:
        self.calls: list[list[float]] = []

    def predict(self, features: list[float]) -> float:
        self.calls.append(features)
        return 0.99


@pytest.fixture
def fake_model() -> FakeModel:
    return FakeModel()


@pytest.fixture
def client(fake_model: FakeModel):
    """TestClient con el modelo real reemplazado por el FakeModel."""
    app.dependency_overrides[get_model] = lambda: fake_model
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
