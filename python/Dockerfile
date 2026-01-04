FROM python:3.12.3

WORKDIR /app

COPY faust_requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY ./filter.py .

RUN mkdir /opt/certs && chmod 777 /opt/certs
