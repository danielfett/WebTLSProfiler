FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y redis && apt-get clean

WORKDIR /usr/src

ADD . /usr/src/webtlsprofiler

WORKDIR /usr/src/webtlsprofiler

RUN pip install --no-cache-dir -r requirements.txt

RUN chown -R 1000:2000 /usr/src/webtlsprofiler

EXPOSE 8000
USER 1000:2000

CMD ./run.sh
