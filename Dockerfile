FROM python:3-alpine

RUN apk update && \
    apk upgrade && \
    apk --no-cache add git bash && \
    rm -rf /var/cache/apk/* && \
    pip install virtualenv

RUN virtualenv /env

RUN git clone https://github.com/osks/pylyskom.git && \
    cd pylyskom && \
    /env/bin/pip install -r requirements.txt && \
    /env/bin/python3 setup.py develop

COPY . /httpkom

RUN cd httpkom && \
    /env/bin/pip install -r requirements.txt && \
    /env/bin/python3 setup.py develop

ENTRYPOINT ["/env/bin/python3", "-m", "httpkom.main", "--config", "/httpkom/configs/debug.cfg"]
CMD []
