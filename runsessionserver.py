#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import zerorpc

from pylyskomrpc.server import run_session_server


logger = logging.getLogger()


def setup_logging():
    #logging.basicConfig()

    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    #root_logger = logging.getLogger()
    #root_logger.addHandler(ch)

    #pylyskomrpc_logger = logging.getLogger('pylyskomrpc')
    #pylyskomrpc_logger.addHandler(ch)

    zerorpc_logger = logging.getLogger('zerorpc')
    zerorpc_logger.addHandler(ch)


if __name__ == "__main__":
    setup_logging()
    run_session_server()
