# Nivel 3 · CI/CD — Pruebas unitarias + GitHub Actions

**Estudiante:** Juliana Rueda  
**Curso:** MLOps — Pontificia Universidad Javeriana  
**Repositorio:** https://github.com/julianaruedag60/mlops-course-repo  
**Imagen Docker Hub:** https://hub.docker.com/r/julianarueda/mlops-preprocessing-api

Este entregable contiene una mini API de **preprocesamiento** en FastAPI con pruebas
unitarias (`pytest`) y un pipeline de **CI/CD en GitHub Actions**. El pipeline ejecuta las
pruebas en cada Pull Request y, al hacer merge a `main`, publica la imagen en Docker Hub.

## Contenido

- [Estructura del proyecto](#estructura-del-proyecto)
- [Actividad 1 · Pruebas unitarias](#actividad-1--pruebas-unitarias)
- [Actividad 2 · GitHub Actions](#actividad-2--github-actions)
- [Reto · Merge bloqueado por una prueba fallida](#reto--merge-bloqueado-por-una-prueba-fallida)
- [Resumen de cumplimiento](#resumen-de-cumplimiento)

---

## Estructura del proyecto

```text
mlops-course-repo/
├── .github/workflows/
│   └── ci-cd-unit-tests-dockerhub.yml   # pipeline CI/CD
└── assignment_3_cicd/
    ├── app.py                           # funciones de preprocesamiento + API FastAPI
    ├── tests/
    │   ├── conftest.py                  # fixtures: FakeModel + TestClient
    │   ├── test_preprocessing.py        # 18 pruebas de las funciones
    │   └── test_api.py                  # 6 pruebas de los endpoints
    ├── requirements.txt
    ├── pytest.ini
    ├── Dockerfile                       # CMD ["pytest"]
    ├── .dockerignore
    └── evidencias/                      # capturas de pantalla
```

---

## Actividad 1 · Pruebas unitarias

### Paso 1 — Funciones de preprocesamiento (`app.py`)

| Función | Tipo | Qué hace |
|---|---|---|
| `clean_text` | Limpieza de texto | Minúsculas, quita tildes, URLs, signos de puntuación y espacios repetidos |
| `validate_range` | Validación de rangos numéricos | Lanza `ValueError` si el valor es nulo/NaN o está fuera de `[min, max]` |
| `min_max_scale` | Transformación de features | Escala un valor numérico al rango `[0, 1]` |
| `one_hot_encode` | Transformación de features | Codifica el segmento (`bronze`, `silver`, `gold`) como vector one-hot |
| `build_features` | Pipeline | Valida + escala + codifica → vector de 6 features |

### Paso 2 — Exponer las funciones en FastAPI

| Método | Ruta | Entrada | Salida |
|---|---|---|---|
| GET | `/health` | — | `{"status": "ok"}` |
| POST | `/clean-text` | `{"text": "..."}` | texto limpio |
| POST | `/preprocess` | `{"age", "income", "score", "segment"}` | vector de features |
| POST | `/predict` | `{"age", "income", "score", "segment"}` | features + predicción |

El modelo se inyecta en `/predict` con `Depends(get_model)`.

### Paso 3 — Pruebas con `TestClient`, aislando el modelo con un fixture

En `tests/conftest.py` el fixture `client` reemplaza el modelo real por un `FakeModel`:

```python
app.dependency_overrides[get_model] = lambda: fake_model
```

Así las pruebas del API no dependen del modelo real. Además se verifica que el modelo
**no se llama** cuando los datos de entrada son inválidos.

**Total: 24 pruebas** (18 de funciones + 6 del API), con casos normales, de borde
(string vacío, límites del rango, NaN, rango degenerado, payload incompleto) y de error
con `pytest.raises` (`TypeError` y `ValueError`).

### Paso 4 — Ejecutar las pruebas en local

```bash
cd assignment_3_cicd
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Resultado esperado: `24 passed`.

![Pruebas en local](evidencias/01_pytest_local.png)

### Paso 5 — Ejecutar las pruebas en contenedor

El `Dockerfile` instala las dependencias y ejecuta `pytest` automáticamente (`CMD ["pytest"]`),
sin intervención manual.

```bash
cd assignment_3_cicd
docker build -t preprocessing-api:0.0.1 .
docker run --rm preprocessing-api:0.0.1
```

![Pruebas dentro del contenedor](evidencias/02_pytest_contenedor.png)

> Las pruebas en contenedor también se ejecutan en GitHub Actions, en el paso
> *Run unit tests inside Docker container* del job `unit-tests`.

---

## Actividad 2 · GitHub Actions

Workflow: [`.github/workflows/ci-cd-unit-tests-dockerhub.yml`](../.github/workflows/ci-cd-unit-tests-dockerhub.yml)

### Flujo del pipeline

```text
push / pull_request con cambios en assignment_3_cicd/**
        │
        ▼
  unit-tests ── pytest en el runner (Ubuntu)
             └─ docker build + docker run (pytest dentro del contenedor)
        │
        │  solo si las pruebas pasan Y es un push a main
        ▼
  publish-dockerhub ── build & push → julianarueda/mlops-preprocessing-api:latest
                                      julianarueda/mlops-preprocessing-api:<sha>
```

### Paso 1 — Módulo Python propio con pruebas unitarias

Se usa el módulo `assignment_3_cicd/` de la Actividad 1.

### Paso 2 — Ajustar `paths` y `APP_PATH`

```yaml
on:
  push:
    branches: [main, "feature/**"]
    paths:
      - "assignment_3_cicd/**"
      - ".github/workflows/ci-cd-unit-tests-dockerhub.yml"
  pull_request:
    branches: [main]
    paths:
      - "assignment_3_cicd/**"
      - ".github/workflows/ci-cd-unit-tests-dockerhub.yml"

env:
  APP_PATH: "assignment_3_cicd"
```

### Paso 3 — Cambiar `IMAGE_NAME` por el usuario de Docker Hub

```yaml
env:
  IMAGE_NAME: "julianarueda/mlops-preprocessing-api"
```

Credenciales configuradas como secrets del repositorio
(**Settings → Secrets and variables → Actions**):

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN` (personal access token de Docker Hub con permiso *Read & Write*)

![Secrets configurados en GitHub](evidencias/03_github_secrets.png)

### Paso 4 — Crear un Pull Request y validar que ejecuta las pruebas

Se abrió el [PR #1](https://github.com/julianaruedag60/mlops-course-repo/pull/1) desde la rama
`feature/assignment-3-cicd` hacia `main`. El job `unit-tests` se ejecutó automáticamente y pasó.
El job `publish-dockerhub` se omite en los PR, como se espera.

**Evidencia 1 — Ejecución exitosa del job `unit-tests`**

![Job unit-tests exitoso en el PR](evidencias/04_unit_tests_pr.png)

### Paso 5 — Hacer merge a `main` y validar que publica la imagen

Al hacer merge del PR #1, el workflow se ejecutó con un `push` a `main`: primero `unit-tests`
y luego `publish-dockerhub`, que construyó y publicó la imagen.

**Evidencia 2 — Job `publish-dockerhub` en `main`**

![Job publish-dockerhub exitoso en main](evidencias/05_publish_dockerhub_main.png)

**Evidencia 3 — Imagen en Docker Hub con tags `latest` y `<sha>`**

Enlace: https://hub.docker.com/r/julianarueda/mlops-preprocessing-api/tags

| Tag | Descripción |
|---|---|
| `latest` | Última versión publicada desde `main` |
| `05e569a3325320b050858cbbe936192986d2e0df` | SHA del commit de merge del PR #1 |

![Imagen en Docker Hub con sus tags](evidencias/06_dockerhub_tags.png)

---

## Reto · Merge bloqueado por una prueba fallida

### 1. Proteger la rama `main`

En **Settings → Branches** se creó una regla de protección para `main` con
**Require status checks to pass before merging**, usando como check requerido `unit-tests`.

![Regla de protección de main](evidencias/07_branch_protection.png)

### 2. Romper una prueba a propósito en un PR

En la rama `feature/reto-prueba-falla` se modificó una aserción en
`tests/test_preprocessing.py` para que falle:

```python
# antes
assert clean_text("ver https://bbva.com ahora") == "ver ahora"
# después (falla a propósito)
assert clean_text("ver https://bbva.com ahora") == "ver AHORA"
```

Se abrió el [PR #2](https://github.com/julianaruedag60/mlops-course-repo/pull/2) hacia `main`.

### 3. Resultado: el job falla y el merge queda bloqueado

El job `unit-tests` falla (`1 failed, 23 passed`) y GitHub bloquea el merge porque el check
requerido no pasó.

![Log de la prueba fallida](evidencias/08_reto_log_fallo.png)

![PR con el merge bloqueado](evidencias/09_reto_merge_bloqueado.png)

El PR #2 se cerró sin hacer merge, así que `main` se mantiene con todas las pruebas en verde.

---

## Resumen de cumplimiento

### Actividad 1

| # | Requisito | Cumplimiento |
|---|---|---|
| 1 | `app.py` (o módulo equivalente) | ✅ `assignment_3_cicd/app.py` |
| 2 | Carpeta `tests/` con mínimo 6 pruebas | ✅ 24 pruebas |
| 3 | Al menos 1 caso de error con `pytest.raises` | ✅ 6 casos (`TypeError`, `ValueError`) |
| 4 | `Dockerfile` que ejecute `pytest` | ✅ `CMD ["pytest"]` |
| 5 | Ejecución exitosa en contenedor | ✅ Local y en GitHub Actions |
| — | Endpoint FastAPI probado con `TestClient` | ✅ `tests/test_api.py` |
| — | Modelo aislado con un fixture | ✅ `FakeModel` en `tests/conftest.py` |

### Actividad 2

| # | Paso | Cumplimiento |
|---|---|---|
| 1 | Módulo Python propio con pruebas | ✅ `assignment_3_cicd/` |
| 2 | Ajustar `paths` y `APP_PATH` | ✅ `assignment_3_cicd/**` |
| 3 | Cambiar `IMAGE_NAME` | ✅ `julianarueda/mlops-preprocessing-api` |
| 4 | PR que ejecuta las pruebas | ✅ PR #1, job `unit-tests` |
| 5 | Merge a `main` que publica la imagen | ✅ Job `publish-dockerhub` |
| Reto | Prueba fallida bloquea el merge | ✅ PR #2 bloqueado |
