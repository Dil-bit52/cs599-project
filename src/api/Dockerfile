FROM python:3.11-slim

WORKDIR /app

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
ENV PIP_DEFAULT_TIMEOUT=120

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 \
    -i ${PIP_INDEX_URL} --trusted-host ${PIP_TRUSTED_HOST} \
    -r requirements.txt

COPY app ./app

ENV RESEARCHPILOT_DATA_DIR=/app/data
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
