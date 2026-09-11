FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

COPY pyproject.toml README.md ./
COPY analyzer ./analyzer
COPY intellireview_cli ./intellireview_cli
COPY app.py ./
COPY mock_review.txt ./
COPY assets ./assets
COPY lib ./lib
COPY sample_repo ./sample_repo

RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
