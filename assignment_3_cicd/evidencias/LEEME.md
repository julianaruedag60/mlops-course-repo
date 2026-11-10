# Evidencias

Subir aquí las capturas con estos nombres exactos (PNG) para que se vean en el README:

| Archivo | Qué capturar |
|---|---|
| `01_pytest_local.png` | Terminal con `pytest` → `24 passed` |
| `02_pytest_contenedor.png` | `docker run` con `24 passed`, o el paso *Run unit tests inside Docker container* en Actions |
| `03_github_secrets.png` | Settings → Secrets: `DOCKERHUB_TOKEN` y `DOCKERHUB_USERNAME` |
| `04_unit_tests_pr.png` | Job `unit-tests` en verde en el PR #1 |
| `05_publish_dockerhub_main.png` | Job `publish-dockerhub` en verde en `main` |
| `06_dockerhub_tags.png` | Docker Hub con los tags `latest` y `<sha>` |
| `07_branch_protection.png` | Regla de protección de `main` con check `unit-tests` |
| `08_reto_log_fallo.png` | Log del job con `FAILED test_clean_text_elimina_urls` |
| `09_reto_merge_bloqueado.png` | PR #2 con el check en rojo y el merge bloqueado |
