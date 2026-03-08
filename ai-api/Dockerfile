FROM python:3.9 AS base

FROM base AS build
WORKDIR /code

RUN pip install pyarmor

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
RUN pyarmor gen /code/app/*

FROM base as final
WORKDIR /dist

COPY ./requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt
COPY --from=build /code/dist /dist
COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]