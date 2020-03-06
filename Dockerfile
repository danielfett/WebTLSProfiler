FROM python:3.7-buster

RUN apt update && apt install -y git redis

WORKDIR /usr/src

RUN git clone https://github.com/fabian-hk/nassl.git

WORKDIR /usr/src/nassl

RUN git checkout tls_profiler

RUN pip install invoke requests

RUN invoke build.all

RUN pip install .

WORKDIR /usr/src/webtlsprofiler

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chown -R 1000:2000 /usr/src/webtlsprofiler

EXPOSE 8000
USER 1000:2000

CMD ./run.sh
