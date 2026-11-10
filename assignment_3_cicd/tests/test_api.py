"""Pruebas del API con TestClient, aislando el modelo con un fixture."""

VALID_PAYLOAD = {"age": 60, "income": 500_000, "score": 0.5, "segment": "silver"}


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_clean_text_endpoint(client) -> None:
    response = client.post("/clean-text", json={"text": "¡Excelente PRODUCTO!!"})
    assert response.status_code == 200
    assert response.json() == {"clean_text": "excelente producto"}


def test_preprocess_endpoint(client) -> None:
    response = client.post("/preprocess", json=VALID_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["features"] == [0.5, 0.5, 0.5, 0.0, 1.0, 0.0]


def test_predict_usa_modelo_aislado(client, fake_model) -> None:
    response = client.post("/predict", json=VALID_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["prediction"] == 0.99
    assert fake_model.calls == [[0.5, 0.5, 0.5, 0.0, 1.0, 0.0]]


def test_predict_fuera_de_rango_devuelve_422(client, fake_model) -> None:
    response = client.post("/predict", json={**VALID_PAYLOAD, "age": 200})
    assert response.status_code == 422
    assert "fuera de rango" in response.json()["detail"]
    assert fake_model.calls == []  # el modelo no se llama con datos inválidos


def test_predict_payload_incompleto(client) -> None:
    response = client.post("/predict", json={"age": 30})
    assert response.status_code == 422
