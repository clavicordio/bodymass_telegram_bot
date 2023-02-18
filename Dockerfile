FROM python:3.10-slim-bullseye

WORKDIR /app

USER 0

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY main.py .
COPY src/*.py src/
COPY data/bodymass.sql data/

CMD python3 main.py;
