"""Pruebas unitarias de las funciones de preprocesamiento."""

import math

import pytest

from app import build_features, clean_text, min_max_scale, one_hot_encode, validate_range


# ---------------------------- clean_text ----------------------------------
def test_clean_text_normaliza_mayusculas_tildes_y_signos() -> None:
    assert clean_text("  ¡Hola, MUNDO! Canción  ") == "hola mundo cancion"


def test_clean_text_elimina_urls() -> None:
    assert clean_text("ver https://bbva.com ahora") == "ver AHORA"  # RETO: falla a propósito


def test_clean_text_string_vacio() -> None:  # caso borde
    assert clean_text("   ") == ""


def test_clean_text_tipo_invalido() -> None:
    with pytest.raises(TypeError):
        clean_text(123)  # type: ignore[arg-type]


# -------------------------- validate_range --------------------------------
def test_validate_range_valor_valido() -> None:
    assert validate_range(30, 0, 120) == 30.0


@pytest.mark.parametrize("value", [0, 120])
def test_validate_range_limites_incluidos(value: float) -> None:  # caso borde
    assert validate_range(value, 0, 120) == float(value)


@pytest.mark.parametrize("value", [-1, 121, math.nan])
def test_validate_range_fuera_de_rango(value: float) -> None:
    with pytest.raises(ValueError):
        validate_range(value, 0, 120)


def test_validate_range_limites_invertidos() -> None:
    with pytest.raises(ValueError, match="min_value"):
        validate_range(5, 10, 0)


# -------------------------- min_max_scale ---------------------------------
@pytest.mark.parametrize(
    "value, expected",
    [(0, 0.0), (50, 0.5), (100, 1.0)],
)
def test_min_max_scale(value: float, expected: float) -> None:
    assert min_max_scale(value, 0, 100) == expected


def test_min_max_scale_rango_degenerado() -> None:  # caso borde
    assert min_max_scale(5, 5, 5) == 0.0


# -------------------------- one_hot_encode --------------------------------
def test_one_hot_encode_normaliza_categoria() -> None:
    assert one_hot_encode("  GOLD ") == [0, 0, 1]


def test_one_hot_encode_categoria_desconocida() -> None:
    with pytest.raises(ValueError, match="desconocida"):
        one_hot_encode("platinum")


# -------------------------- build_features --------------------------------
def test_build_features_vector_completo() -> None:
    assert build_features(60, 500_000, 0.5, "silver") == [0.5, 0.5, 0.5, 0.0, 1.0, 0.0]
