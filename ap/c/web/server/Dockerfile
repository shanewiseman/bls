from tiangolo/uwsgi-nginx-flask:python3.7

WORKDIR /app/
COPY ./app/Pipfile* ./

RUN pip install pipenv && pipenv install --deploy --system && pip uninstall pipenv -y


COPY ./app .
WORKDIR /app

