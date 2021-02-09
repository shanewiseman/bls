FROM python:3
WORKDIR /app/
COPY Pipfile* ./ 
RUN pip install pipenv && \
    apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev libssl-dev && \ 
    pipenv install --deploy --system  && \
    apt-get remove -y gcc python3-dev libssl-dev && \
    apt-get autoremove -y && \
    pip uninstall pipenv -y
COPY data/ ./data/

COPY app.py app.py
CMD ["python", "app.py"]
