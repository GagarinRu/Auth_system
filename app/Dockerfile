FROM python:3.12.8

RUN groupadd -g 1000 app_group \
    && useradd -r -u 1000 -g app_group -m -s /sbin/nologin app_user

RUN mkdir -p /app && chown -R app_user:app_group /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install uv

COPY --chown=app_user:app_group pyproject.toml ./

RUN uv pip compile pyproject.toml -o requirements.txt && \
    uv pip install --system -r requirements.txt && \
    pip cache purge

COPY --chown=app_user:app_group src/ .

COPY --chown=app_user:app_group entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

USER app_user

ENTRYPOINT ["/entrypoint.sh"]