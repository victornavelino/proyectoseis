FROM python:3.10-alpine
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		postgresql-client \
	&& rm -rf /var/lib/apt/lists/*
WORKDIR /carniceriavv
COPY requirements.txt /carniceriavv/

