from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from mlflow.exceptions import MlflowException
from pydantic import BaseModel, ConfigDict, Field

from inference import load_model, model_info, predict_penguin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The model may not be registered yet; /predict and /model/reload retry later.
    try:
        load_model()
    except MlflowException:
        pass
    yield


app = FastAPI(title="Palmer Penguins API", lifespan=lifespan)


class PenguinFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"island": "Torgersen", "bill_length_mm": 39.1, "bill_depth_mm": 18.7, "flipper_length_mm": 181, "body_mass_g": 3750, "sex": "MALE"}]})
    island: Literal["Biscoe", "Dream", "Torgersen"] = Field(examples=["Torgersen"])
    bill_length_mm: float = Field(examples=[39.1])
    bill_depth_mm: float = Field(examples=[18.7])
    flipper_length_mm: float = Field(examples=[181])
    body_mass_g: float = Field(examples=[3750])
    sex: Literal["MALE", "FEMALE"] = Field(examples=["MALE"])


@app.get("/health")
def health():
    return {"status": "ok", "model": model_info()}


@app.get("/model")
def model():
    return model_info()


@app.post("/model/reload")
def reload_model():
    try:
        return load_model()
    except MlflowException as error:
        raise HTTPException(503, f"Model not available in MLflow. Run notebooks/entrenamiento.ipynb first. ({error.message})") from error


@app.post("/predict")
def predict(features: PenguinFeatures):
    try:
        species = predict_penguin(features.model_dump())
        return {"model": model_info(), "predicted_species": species}
    except MlflowException as error:
        raise HTTPException(503, f"Model not available in MLflow. Run notebooks/entrenamiento.ipynb first. ({error.message})") from error
