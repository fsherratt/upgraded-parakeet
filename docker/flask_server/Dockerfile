FROM python:3.7-alpine3.12

COPY . /app
WORKDIR /app

# https://wired-world.com/?p=100
RUN apk add --update curl gcc g++
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

RUN pip install -r requirements.txt