"""Mini API de preprocesamiento para MLOps (Actividad 1 · Pruebas unitarias).

Funciones de preprocesamiento:
    1. clean_text          -> limpieza de texto
    2. validate_range      -> validación de rangos numéricos
    3. min_max_scale       -> transformación de features (escalado 0-1)
    4. one_hot_encode      -> transformación de features categóricas

Se exponen en FastAPI y el modelo se inyecta con `Depends(get_model)`,
lo que permite aislarlo en las pruebas con un fixture.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Protocol

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

# --------------------------------------------------------------------------
# Rangos válidos de las features numéricas
# --------------------------------------------------------------------------
FEATURE_RANGES: dict[str, tuple[float, float]] = {
    "age": (0, 120),
    "income": (0, 1_000_000),
    "score": (0, 1),
}

CATEGORIES: list[str] = ["bronze", "silver", "gold"]


# --------------------------------------------------------------------------
# 1. Limpieza de texto
# --------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Normaliza un texto: minúsculas, sin tildes, sin URLs, sin signos
    de puntuación y con espacios colapsados."""
    if not isinstance(text, str):
        raise TypeError("text debe ser un string")

    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9ñ\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------------
# 2. Validación de rangos numéricos
# --------------------------------------------------------------------------
def validate_range(value: float, min_value: float, max_value: float) -> float:
    """Devuelve el valor si está en [min_value, max_value]; si no, ValueError."""
    if min_value > max_value:
        raise ValueError("min_value no puede ser mayor que max_value")
    if value is None or value != value:  # None o NaN
        raise ValueError("value no puede ser nulo ni NaN")
    if not min_value <= value <= max_value:
        raise ValueError(
            f"value={value} fuera de rango [{min_value}, {max_value}]"
        )
    return float(value)


# --------------------------------------------------------------------------
# 3. Transformación de features
# --------------------------------------------------------------------------
def min_max_scale(value: float, min_value: float, max_value: float) -> float:
    """Escala un valor al rango [0, 1] usando min-max scaling."""
    validate_range(value, min_value, max_value)
    if max_value == min_value:
        return 0.0
    return round((value - min_value) / (max_value - min_value), 4)


def one_hot_encode(category: str, categories: list[str] = CATEGORIES) -> list[int]:
    """Codifica una categoría como vector one-hot."""
    normalized = clean_text(category)
    if normalized not in categories:
        raise ValueError(f"categoría desconocida: {category!r}")
    return [1 if c == normalized else 0 for c in categories]


def build_features(age: float, income: float, score: float, segment: str) -> list[float]:
    """Pipeline completo: valida, escala y codifica -> vector de features."""
    scaled = [
        min_max_scale(age, *FEATURE_RANGES["age"]),
        min_max_scale(income, *FEATURE_RANGES["income"]),
        min_max_scale(score, *FEATURE_RANGES["score"]),
    ]
    return scaled + [float(x) for x in one_hot_encode(segment)]


# --------------------------------------------------------------------------
# Modelo (dependencia inyectable)
# --------------------------------------------------------------------------
class Model(Protocol):
    def predict(self, features: list[float]) -> float: ...


class LinearModel:
    """Modelo lineal simple. En producción aquí se cargaría un .pkl/.joblib."""

    def __init__(self) -> None:
        self.weights = [0.2, 0.3, 0.4, 0.0, 0.05, 0.1]
        self.bias = 0.0

    def predict(self, features: list[float]) -> float:
        return round(sum(w * x for w, x in zip(self.weights, features)) + self.bias, 4)


_model: Model | None = None


def get_model() -> Model:
    """Dependencia de FastAPI: carga el modelo una sola vez."""
    global _model
    if _model is None:
        _model = LinearModel()
    return _model


# --------------------------------------------------------------------------
# API FastAPI
# --------------------------------------------------------------------------
app = FastAPI(title="Preprocessing API", version="1.0.0")


class TextIn(BaseModel):
    text: str


class FeaturesIn(BaseModel):
    age: float
    income: float
    score: float
    segment: str = Field(..., examples=["gold"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/clean-text")
def clean_text_endpoint(payload: TextIn) -> dict:
    return {"clean_text": clean_text(payload.text)}


@app.post("/preprocess")
def preprocess_endpoint(payload: FeaturesIn) -> dict:
    try:
        features = build_features(payload.age, payload.income, payload.score, payload.segment)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"features": features}


@app.post("/predict")
def predict_endpoint(payload: FeaturesIn, model: Model = Depends(get_model)) -> dict:
    try:
        features = build_features(payload.age, payload.income, payload.score, payload.segment)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"features": features, "prediction": model.predict(features)}
