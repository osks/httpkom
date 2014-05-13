# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

import logging

import zerorpc

from komsessionstorage import InMemoryKomSessionStorage, KomSessionStorageServer


logger = logging.getLogger(__name__)


def setup_logging():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    zerorpc_logger = logging.getLogger('zerorpc')
    zerorpc_logger.addHandler(ch)


def run_storage_server():
    storage = InMemoryKomSessionStorage()
    storage_server = KomSessionStorageServer(storage)

    rpcserver = zerorpc.Server(storage_server)
    rpcserver.bind('tcp://127.0.0.1:12345')
    rpcserver.run()


if __name__ == "__main__":
    setup_logging()
    run_storage_server()
