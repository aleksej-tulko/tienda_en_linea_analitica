FROM python:3.12.3

WORKDIR /app

COPY faust_requirements.txt .

RUN pip install -r faust_requirements.txt --no-cache-dir

COPY ./faust_filter.py .

RUN mkdir /opt/certs && chmod 777 /opt/certs
