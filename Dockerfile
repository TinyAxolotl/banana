FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-requests \
    python3-yaml \
    && apt-get clean

COPY ./banana/ /app/banana/
COPY setup.py /app/
WORKDIR /app/
RUN pip3 install --no-deps .
