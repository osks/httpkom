#!/usr/bin/env python

import logging
import sys
import time

import gevent

from pylyskomrpc.client import create_client


logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)


def create(client):
    logger.debug("create")
    ks_id = client.create_session()
    ks = client.get_session(ks_id)

    ks.connect("localhost", 4894,
               "oskar", "localhost",
               "test", "0.1")
    person_no = ks.lookup_name_exact("oskars testperson", want_pers=True, want_confs=False)
    ks.login(person_no, "oxide24")
    return ks_id


def do(client, ks_id):
    logger.debug("do")
    ks = client.get_session(ks_id)
    #gevent.sleep(0.1)
    confs = ks.lookup_name("", True, True)
    ks.logout()


def delete(client, ks_id):
    logger.debug("destroy")
    ks = client.get_session(ks_id)

    logger.debug("disconnecting")
    ks.disconnect()
    
    logger.debug("deleting komsession")
    client.delete_session(ks_id)
    

def run_test2():
    client = create_client()

    ks_id1 = create(client)
    logger.debug("sleeping")
    gevent.sleep(5)
    ks_id2 = create(client)

    logger.debug("sleeping")
    gevent.sleep(5)

    delete(client, ks_id2)
    logger.debug("sleeping")
    gevent.sleep(5)
    delete(client, ks_id1)

    client.close()


def run_test1():
    client = create_client()
    def _run():
        ks_id = create(client)
        do(client, ks_id)
        delete(client, ks_id)

    gevent.joinall([ gevent.spawn(_run) for i in range(100) ])
    client.close()


def run_test3():
    client = create_client()
    ks_id1 = create(client)

    client.stream(ks_id1)

    delete(client, ks_id1)
    client.close()


def run_test4():
    client = create_client()
    ks_id = client.create_session()
    ks = client.get_session(ks_id)

    host = "kom.lysator.liu.se"
    ks.connect(host, 4894,
               "oskar", "localhost",
               "test", "0.1")
    #person_no = ks.lookup_name_exact("oskars testperson", want_pers=True, want_confs=False)
    person_no = 14506
    ks.login(person_no, "oxide24")

    memberships = ks.get_memberships(14506, 0, 100, True, False)
    unreads = ks.get_membership_unreads(14506)
    unread = ks.get_membership_unread(14506, 14506)

    delete(client, ks_id)
    client.close()

def run():
    logger.debug("starting")

    #run_test1()
    #run_test2()
    #run_test3()
    run_test4()

    logger.debug("done.")


if __name__ == "__main__":
    setup_logging()
    run()
