FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# El contenedor ejecuta las pruebas sin intervención manual
CMD ["pytest"]
