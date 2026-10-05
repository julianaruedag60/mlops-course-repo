# Assignment 3

Ejecuta todos los comandos desde la carpeta `assignment3`.

Clasificador de especies de pingüinos entrenado en JupyterLab, con experimentos y modelos registrados en MLflow, y servido por una API en FastAPI que carga el modelo desde el Model Registry de MLflow.

## Arquitectura

| Servicio | Contenedor | Función | Puerto local |
|---|---|---|---|
| `data-db` | `penguins-mysql` | MySQL con los datos crudos y procesados de pingüinos | 3307 |
| `mlflow-db` | `mlflow-postgres` | Postgres con la metadata de MLflow (experimentos, ejecuciones, registro de modelos) | 5432 |
| `storage` | `mlflow-minio` | MinIO con los artefactos de MLflow (bucket `mlflow-artifacts`) | 8013 (S3), 8014 (consola) |
| `create-bucket` | `mlflow-create-bucket` | Tarea que se ejecuta una sola vez para crear el bucket en MinIO | - |
| `mlflow` | `mlflow-server` | Servidor de tracking y Model Registry de MLflow | 5002 |
| `jupyter` | `mlflow-jupyter` | JupyterLab para cargar los datos y entrenar los modelos | 8889 |
| `api` | `penguins-api` | API de inferencia que usa `models:/penguins-classifier@production` | 8002 |

```text
penguins.csv ──► MySQL (penguins_raw ─► penguins_processed)
                                 │
                                 ▼
                JupyterLab (24 ejecuciones de entrenamiento)
                                 │
                                 ▼
          MLflow ──► Postgres (metadata) + MinIO (modelos)
                                 │
                                 ▼
                    FastAPI ──► /predict
```

## Configuración inicial

```bash
cp .env.example .env
```

Descarga el CSV en la carpeta `data` **antes del primer `docker compose up`**:

```bash
curl -L --retry 3 -o data/penguins.csv \
  https://cdn.jsdelivr.net/gh/mwaskom/seaborn-data@master/penguins.csv
```

MySQL carga este CSV automáticamente en la tabla `penguins_raw` la primera vez que arranca (ver [Carga automática de datos](#carga-automática-de-datos)).

## Construir y levantar

```bash
docker compose up -d --build
docker compose ps
```

El nombre del proyecto es `mlflow-stack` (definido en `docker-compose.yaml`), así los contenedores, volúmenes y la red `mlflow-network` no chocan con otros proyectos de Docker Compose.

| Interfaz | URL | Credenciales |
|---|---|---|
| JupyterLab | <http://localhost:8889/?token=mlflow> | token `mlflow` |
| MLflow | <http://localhost:5002> | - |
| Consola de MinIO | <http://localhost:8014> | `s3admin` / `s3admin123` |
| Documentación de la API | <http://localhost:8002/docs> | - |

## Entrenar los modelos

Abre `notebooks/entrenamiento.ipynb` en JupyterLab y ejecuta **Run → Run All Cells**. El notebook:

1. Verifica que `penguins_raw` ya esté en MySQL (la carga MySQL al arrancar, no el notebook).
2. Lee `penguins_raw` desde MySQL, elimina valores faltantes, valores inválidos de `sex` y duplicados, aplica one-hot encoding a `island` y `sex`, y guarda el resultado en `penguins_processed`.
3. Lee `penguins_processed` desde MySQL y entrena 24 modelos en el experimento de MLflow `penguins-taller`, registrando en cada ejecución los parámetros, las métricas (`test_accuracy`, `test_f1_macro`, `train_accuracy`) y el modelo:

   | Modelo | Hiperparámetros | Ejecuciones |
   |---|---|---|
   | `LogisticRegression` | `C` ∈ {0.001, 0.01, 0.1, 1, 10, 100} | 6 |
   | `KNeighborsClassifier` | `n_neighbors` ∈ {1, 3, 5, 9, 15, 25} | 6 |
   | `RandomForestClassifier` | `n_estimators` ∈ {10, 50, 200} × `max_depth` ∈ {1, 2, 4, None} | 12 |

4. Registra la mejor ejecución (mayor `test_f1_macro`, luego mayor `test_accuracy` y luego menor diferencia entre train y test) como `penguins-classifier` y le asigna el alias `production`.

También se puede ejecutar desde la terminal:

```bash
docker compose exec jupyter jupyter nbconvert --to notebook --execute --inplace \
  /workspace/notebooks/entrenamiento.ipynb
```

El notebook `notebooks/probar_modelos.ipynb` carga los modelos registrados en MLflow y hace una predicción de ejemplo.

## Carga automática de datos

El servicio `data-db` monta `data/penguins.csv` en `/import` y `mysql/init/` en `/docker-entrypoint-initdb.d`. Cuando MySQL inicializa un volumen vacío, ejecuta `mysql/init/01_penguins_raw.sql`, que crea la tabla `penguins_raw` y carga el CSV con `LOAD DATA INFILE` (los campos vacíos quedan como `NULL`).

El script **solo se ejecuta la primera vez**, cuando el volumen de MySQL está vacío. Para volver a cargar el CSV (por ejemplo, si cambió), borra solo el volumen de MySQL; MLflow no se ve afectado:

```bash
docker compose rm -sf data-db
docker volume rm mlflow-stack_data-db-volume
docker compose up -d data-db
```

Después vuelve a ejecutar el notebook para regenerar `penguins_processed`.

## MySQL: ver los datos de pingüinos

```bash
docker compose exec data-db mysql -u penguins_user -p -D penguins
```

```text
contraseña: penguins_password
```

```sql
SHOW TABLES;
SELECT COUNT(*) FROM penguins_raw;
SELECT * FROM penguins_raw LIMIT 10;

SELECT COUNT(*) FROM penguins_processed;
SELECT * FROM penguins_processed LIMIT 10;
exit
```

## MLflow

- Experimentos: <http://localhost:5002> → `penguins-taller`. Selecciona varias ejecuciones y usa **Compare** para graficar los hiperparámetros contra las métricas.
- Registro de modelos: <http://localhost:5002/#/models/penguins-classifier>.

Para promover otra versión, mueve el alias `production` desde la interfaz de MLflow (versión del modelo → **Aliases**) o desde JupyterLab:

```python
import mlflow
mlflow.MlflowClient().set_registered_model_alias("penguins-classifier", "production", 2)
```

Luego recarga el modelo en la API (ver abajo).

## API

La API carga `models:/penguins-classifier@production` desde MLflow al arrancar. Si el modelo todavía no está registrado, `/predict` responde `503` hasta que se ejecute el notebook.

```bash
curl http://localhost:8002/health
curl http://localhost:8002/model
```

```bash
curl -X POST http://localhost:8002/predict \
  -H 'Content-Type: application/json' \
  -d '{"island":"Torgersen","bill_length_mm":39.1,"bill_depth_mm":18.7,"flipper_length_mm":181,"body_mass_g":3750,"sex":"MALE"}'
```

`island` debe ser `Biscoe`, `Dream` o `Torgersen`; `sex` debe ser `MALE` o `FEMALE`.

Después de reentrenar o de mover el alias `production`:

```bash
curl -X POST http://localhost:8002/model/reload
```

## Volúmenes de Docker

```bash
docker volume ls
docker volume inspect mlflow-stack_data-db-volume
docker volume inspect mlflow-stack_pgdata
docker volume inspect mlflow-stack_storage-data
```

## Detener

```bash
docker compose down
```

## Borrar los volúmenes del Assignment 3

Borra los datos de MySQL, la metadata de MLflow y los artefactos de MLflow.

```bash
docker compose down -v
```

## Versión anterior (Airflow)

El pipeline de Airflow (`dags/`, Airflow + MySQL + API que leía archivos `.pkl` locales) está en el commit `74614f9`. Su demo:

![Demo de la API](files/Demo.gif)
