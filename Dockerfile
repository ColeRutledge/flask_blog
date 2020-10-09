##### Pip Docker-Compose #####

# FROM python:3.8

# ENV PIP_DISABLE_PIP_VERSION_CHECK=on

# EXPOSE 5000

# WORKDIR /app

# COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .


##### Pip No Docker-Compose #####

# FROM python:3.8

# ENV PIP_DISABLE_PIP_VERSION_CHECK=on
#     FLASK_APP=app.py \
#     FLASK_ENV=development \
#     FLASK_RUN_HOST=0.0.0.0

# EXPOSE 5000

# WORKDIR /app

# COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# CMD [ "python", "-m", "flask", "run" ]


##### Pip Docker-Compose w/ VSCode Debugger #####

FROM python:3.8

ENV PIP_DISABLE_PIP_VERSION_CHECK=on

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

EXPOSE 5000

WORKDIR /app
# ADD . /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switches to a non-root user and changes the ownership of the /app folder"
# RUN useradd appuser && chown -R appuser /app
# USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]


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