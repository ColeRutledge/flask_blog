FROM python:3.8-alpine

ENV PIP_DISABLE_PIP_VERSION_CHECK=on
#     FLASK_APP=app.py \
#     FLASK_ENV=development

RUN apk add --no-cache gcc musl-dev linux-headers

EXPOSE 5000

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD [ "python", "-m", "flask", "run"]
# CMD [ "python", "-m", "flask", "run", "--host=0.0.0.0" ]



##### Poetry #####

# FROM python:3.8

# ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
#     POETRY_VERSION=1.1.0
#     FLASK_APP=app.py \
#     FLASK_ENV=development

# EXPOSE 5000

# COPY poetry.lock pyproject.toml /app/
# # RUN poetry export --ouput requirements.txt --without-hashes

# WORKDIR /usr/src/app

# RUN pip install 'poetry==$POETRY_VERSION' && \
#     poetry config virtualenvs.create false && \
#     poetry install --no-interaction
# COPY . .

# COPY . /app

# CMD [ "poetry", "run", "flask", "run", "--host=0.0.0.0" ]
