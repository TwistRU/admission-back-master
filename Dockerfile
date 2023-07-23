FROM python:3.10

WORKDIR /app

RUN apt update && apt install netcat-traditional dnsutils -y

RUN pip install --upgrade pip

RUN pip install poetry

COPY ./poetry.toml ./pyproject.toml ./poetry.lock* /app/

RUN poetry config virtualenvs.create false --local
RUN poetry config virtualenvs.create false
RUN poetry config virtualenvs.in-project false --local

RUN poetry update --no-dev

COPY ./app ./app

EXPOSE ${PORT}

CMD poetry run gunicorn -w 1 -b 0.0.0.0:${PORT} -k uvicorn.workers.UvicornWorker -t 1200 --threads 4 app.main:app