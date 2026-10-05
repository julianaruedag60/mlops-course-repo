import os

import mlflow
import pandas as pd

MODEL_NAME = os.environ.get("MODEL_NAME", "penguins-classifier")
MODEL_ALIAS = os.environ.get("MODEL_ALIAS", "production")
ISLANDS = ("Biscoe", "Dream", "Torgersen")
SEXES = ("FEMALE", "MALE")

state = {"model": None, "version": None, "run_id": None}


def load_model() -> dict:
    """Fetch the model version pointed to by MODEL_ALIAS from the MLflow registry."""
    version = mlflow.MlflowClient().get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
    state["model"] = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@{MODEL_ALIAS}")
    state["version"] = version.version
    state["run_id"] = version.run_id
    return model_info()


def model_info() -> dict:
    return {"name": MODEL_NAME, "alias": MODEL_ALIAS, "version": state["version"], "run_id": state["run_id"], "loaded": state["model"] is not None}


def preprocess(features: dict) -> pd.DataFrame:
    """Same transformation the training notebook applies to build penguins_processed."""
    row = {key: float(features[key]) for key in ("bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g")}
    row |= {f"island_{island}": float(features["island"] == island) for island in ISLANDS}
    row |= {f"sex_{sex}": float(features["sex"] == sex) for sex in SEXES}
    return pd.DataFrame([row])


def predict_penguin(features: dict) -> str:
    if state["model"] is None:
        load_model()
    return str(state["model"].predict(preprocess(features))[0])
