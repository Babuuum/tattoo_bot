FROM python:3.13-slim

ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock* /app/
RUN poetry install --only main --no-root

COPY . /app

CMD ["uvicorn", "apps.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
