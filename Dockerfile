FROM python:3.9-slim

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

CMD [ "python", "./show_downloader.py", "--config", "/config/config.yaml", "--tracker", "/config/tracker.yaml" ]
