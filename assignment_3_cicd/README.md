# Assignment 3 · CI/CD — Pruebas unitarias + GitHub Actions

Mini API de **preprocesamiento** en FastAPI con pruebas unitarias (`pytest`),
ejecución en contenedor y pipeline de CI/CD que publica la imagen en Docker Hub.

## Estructura

```text
assignment_3_cicd/
├── app.py                    # funciones de preprocesamiento + API FastAPI
├── tests/
│   ├── conftest.py           # fixtures: FakeModel + TestClient con dependency_overrides
│   ├── test_preprocessing.py # pruebas unitarias de las funciones
│   └── test_api.py           # pruebas del API con TestClient
├── requirements.txt
├── pytest.ini
├── Dockerfile                # CMD ["pytest"]
└── .dockerignore

.github/workflows/ci-cd-unit-tests-dockerhub.yml   # pipeline CI/CD
```

---

## Actividad 1 · Pruebas unitarias

### Funciones de preprocesamiento (`app.py`)

| Función | Tipo | Qué hace |
|---|---|---|
| `clean_text` | Limpieza de texto | minúsculas, quita tildes, URLs, signos y espacios repetidos |
| `validate_range` | Validación de rangos | lanza `ValueError` si el valor es nulo/NaN o está fuera de `[min, max]` |
| `min_max_scale` | Transformación de features | escala un valor numérico a `[0, 1]` |
| `one_hot_encode` | Transformación de features | codifica el segmento (`bronze`, `silver`, `gold`) como vector one-hot |
| `build_features` | Pipeline | valida + escala + codifica → vector de 6 features |

### Endpoints FastAPI

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | estado del servicio |
| POST | `/clean-text` | `{"text": "..."}` → texto limpio |
| POST | `/preprocess` | `{"age", "income", "score", "segment"}` → vector de features |
| POST | `/predict` | igual que `/preprocess` + predicción del modelo |

El modelo se inyecta con `Depends(get_model)`. En las pruebas, el fixture `client`
reemplaza el modelo real por un `FakeModel` usando `app.dependency_overrides`,
así las pruebas del API **no dependen del modelo** y además se puede verificar
que el modelo no se llama cuando los datos son inválidos.

### Cumplimiento de requisitos

| # | Requisito | Cómo se cumple |
|---|---|---|
| 1 | `app.py` | `assignment_3_cicd/app.py` |
| 2 | `tests/` con mínimo 6 pruebas | **24 pruebas** (18 de funciones + 6 del API) |
| 3 | ≥ 1 caso de error con `pytest.raises` | `TypeError` en `clean_text`, `ValueError` en `validate_range`, `one_hot_encode` y límites invertidos |
| 4 | `Dockerfile` que ejecute `pytest` | `CMD ["pytest"]` |
| 5 | Ejecución exitosa en contenedor | `docker run` local y paso *Run unit tests inside Docker container* del workflow |

Casos de **borde** cubiertos: string vacío, límites del rango incluidos (0 y 120),
NaN, rango degenerado (`min == max`), categoría con espacios/mayúsculas, payload incompleto.

### Ejecutar local

```bash
cd assignment_3_cicd
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

### Ejecutar en contenedor

```bash
cd assignment_3_cicd
docker build -t preprocessing-api:0.0.1 .
docker run --rm preprocessing-api:0.0.1
```

Resultado esperado: `24 passed`.

### Levantar el API (opcional)

```bash
uvicorn app:app --reload   # requiere: pip install uvicorn
# http://localhost:8000/docs
```

---

## Actividad 2 · GitHub Actions

Workflow: [`.github/workflows/ci-cd-unit-tests-dockerhub.yml`](../.github/workflows/ci-cd-unit-tests-dockerhub.yml)

| Paso | Cambio realizado |
|---|---|
| 1. Módulo Python propio con pruebas | `assignment_3_cicd/` (Actividad 1) |
| 2. Ajustar `paths` y `APP_PATH` | `paths: "assignment_3_cicd/**"` · `APP_PATH: "assignment_3_cicd"` |
| 3. Cambiar `IMAGE_NAME` | `julianarueda/mlops-preprocessing-api` |
| 4. Pull Request que ejecute pruebas | job `unit-tests` en `pull_request` hacia `main` |
| 5. Merge a `main` que publique imagen | job `publish-dockerhub` solo en `push` a `main` y si `unit-tests` pasa |

### Flujo del pipeline

```text
push / pull_request (cambios en assignment_3_cicd/**)
        │
        ▼
  unit-tests  ── pytest en el runner
              └─ docker build + docker run (pytest dentro del contenedor)
        │  (solo si pasa y es push a main)
        ▼
  publish-dockerhub ── build & push  →  julianarueda/mlops-preprocessing-api:latest
                                        julianarueda/mlops-preprocessing-api:<sha>
```

### Configuración previa (una sola vez)

1. En Docker Hub: **Account settings → Personal access tokens → Generate new token** (permiso *Read & Write*).
2. En GitHub, repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `DOCKERHUB_USERNAME` = usuario de Docker Hub
   - `DOCKERHUB_TOKEN` = el token generado
3. (Para el reto) **Settings → Branches → Add branch ruleset / protection rule** sobre `main`:
   activar *Require status checks to pass before merging* y seleccionar el check `unit-tests`.

### Reto: hacer fallar una prueba en un PR

```bash
git switch -c feature/reto-falla
# romper a propósito una aserción, p. ej. en tests/test_preprocessing.py:
#   assert clean_text("ver https://bbva.com ahora") == "ver AHORA"
git commit -am "🧪 test: make a test fail on purpose (reto)"
git push -u origin feature/reto-falla
```

Abrir el PR hacia `main`: el job `unit-tests` queda en rojo y, con la regla de
protección activa, el botón **Merge** queda bloqueado. Cerrar el PR sin hacer merge.

### Evidencias

| Evidencia | Enlace / captura |
|---|---|
| Ejecución exitosa del job `unit-tests` (PR) | _pegar captura_ |
| Job `publish-dockerhub` en `main` | _pegar captura_ |
| Imagen en Docker Hub con tags `latest` y `<sha>` | `https://hub.docker.com/r/julianarueda/mlops-preprocessing-api/tags` |
| Reto: PR con prueba fallida y merge bloqueado | _pegar captura_ |
