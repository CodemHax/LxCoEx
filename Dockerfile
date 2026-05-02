FROM docker:28-cli AS docker_cli

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --from=docker_cli /usr/local/bin/docker /usr/local/bin/docker

COPY . .

EXPOSE 8007
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]


