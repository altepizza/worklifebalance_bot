FROM python:3.12-slim

LABEL org.opencontainers.image.source https://github.com/altepizza/worklifebalance_bot

WORKDIR /app

COPY Pipfile* /app

RUN pip install pipenv

# Install dependencies using pipenv
# --system flag tells pipenv to install the dependencies globally in the docker image
# rather than in a virtualenv, which is the default behavior of pipenv
RUN pipenv install --system --deploy

COPY src/*.py /app
COPY src/settings.toml /app

CMD ["python", "main.py"]
