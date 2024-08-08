ARG VARIANT=3.12
FROM python:${VARIANT}
RUN --mount=source=dist,target=/dist PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /dist/*.whl
CMD python -m gitlabtaskscheduler