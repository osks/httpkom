import asyncio
import json
from json.decoder import JSONDecodeError

from quart import g, jsonify, websocket

from httpkom import HTTPKOM_CONNECTION_HEADER, app
from .sessions import _get_komsession


def _get_connection_id_from_websocket():
    """WebSockets don't support http headers, so we pass the connection id as query param.
    """
    return websocket.args.get(HTTPKOM_CONNECTION_HEADER, None)


@app.websocket('/websocket')
async def ws_new():
    app.logger.debug("Websocket connected")

    g.connection_id = _get_connection_id_from_websocket()
    g.ksession = _get_komsession(g.connection_id)

    if g.ksession is None:
        return error_response(403, error_msg='Invalid connection id')

    try:
        await websocket.accept()
        app.logger.debug("Websocket accepted")
        producer = asyncio.create_task(ws_sending())
        consumer = asyncio.create_task(ws_receiving())
        await asyncio.gather(producer, consumer)
    except asyncio.CancelledError as e:
        # disconnect
        print("Websocket disconnected", e)
        raise
    except Exception as e:
        print("Websocket unknown exception:", e)
        raise


async def ws_sending():
    try:
        while True:
            try:
                message = {"msg": "hej hej"}
                data = json.dumps(message)
                #await websocket.send(data)
                #print(f"Websocket sent: {data!r}")
            except TypeError as te:
                print(f"Failed to json encode {message!r}: {te}")
            except Exception as e:
                print("Failed to send: ", e)

            await asyncio.sleep(3.0)
    except asyncio.CancelledError as e:
        # disconnect
        raise
    except Exception as e:
        print("Websocket sending unknown exception:", e)
        raise


async def ws_receiving():
    """Expects websocket request with json like:

    {
      "protocol": "echo" / "a",
      "ref_no": <int>,
      "request": "...",
    }

    and sends back websocket replies with json like:

    {
      "protocol": "echo" / "a",
      "ref_no": <int>,
      "reply": "...",
    }

    """
    try:
        while True:
            try:
                data = await websocket.receive()
                app.logger.debug(f"Websocket received: {data!r}")
                req_msg = json.loads(data)

                protocol = req_msg.get('protocol')
                if protocol is None:
                    # ignore invalid
                    app.logger.debug("Websocket recieved: invalid, no protocol")
                    continue

                ref_no = req_msg.get('ref_no')
                if ref_no is None:
                    # ignore invalid
                    app.logger.debug("Websocket recieved: invalid, no ref_no")
                    continue

                request = req_msg.get('request')

                if protocol == 'echo':
                    rep_msg = {
                        'protocol': protocol,
                        'ref_no': ref_no,
                        'reply': request,
                    }
                    await websocket.send(json.dumps(rep_msg))
                elif protocol == 'a':
                    reply = await g.ksession.raw_request(request.encode('utf-8'))
                    rep_msg = {
                        'protocol': protocol,
                        'ref_no': ref_no,
                        'reply': reply.decode('utf-8')
                    }
                    await websocket.send(json.dumps(rep_msg))
                else:
                    # ignore invalid
                    app.logger.debug(f"Websocket recieved: invalid, unknown protocol: {protocol}")
                    continue

            except JSONDecodeError as de:
                print(f"Failed to json decode {data!r}: {de}")
                continue
            except Exception as e:
                print("Failed to receive: ", e)
                continue
    except asyncio.CancelledError as e:
        # disconnect
        raise
    except Exception as e:
        print("Websocket receiving unknown exception:", e)
        raise
