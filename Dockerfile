FROM --platform=linux/amd64 python:3.9-slim

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install --no-install-recommends curl wget gnupg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

WORKDIR /usr/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

CMD [ "python", "./show_downloader.py", "--log", "INFO", "--config", "/config/config.yaml", "--tracker", "/config/tracker.yaml" ]
