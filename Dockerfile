FROM python:3.7-buster

RUN apt-get update && apt-get install -y git

WORKDIR /usr/src

RUN git clone https://github.com/fabian-hk/nassl.git

WORKDIR /usr/src/nassl

RUN git checkout tls_profiler

RUN pip install invoke requests

RUN invoke build.all

RUN pip install .

COPY requirements.txt .

RUN pip install -r requirements.txt

FROM python:3.7-slim-buster

RUN apt-get update && apt-get install -y redis && apt-get clean
RUN pip install gunicorn

COPY --from=0 /usr/local/lib/python3.7/ /usr/local/lib/python3.7/

WORKDIR /usr/src/webtlsprofiler

COPY . .

RUN chown -R 1000:2000 /usr/src/webtlsprofiler

EXPOSE 8000
USER 1000:2000

CMD ./run.sh
