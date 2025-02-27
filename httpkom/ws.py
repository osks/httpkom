import asyncio
import json
from json.decoder import JSONDecodeError
from typing import Dict, Optional

from quart import g, jsonify, websocket

from httpkom import HTTPKOM_CONNECTION_HEADER, app
from .sessions import _get_komsession


def _get_connection_id_from_websocket():
    """WebSockets don't support http headers, so we pass the connection id as query param.
    """
    return websocket.args.get(HTTPKOM_CONNECTION_HEADER, None)


class WebSocketConnection:
    def __init__(self, ws, komsession):
        self.ws = ws
        self.komsession = komsession
        self.tasks: Dict[str, asyncio.Task] = {}

    async def handle_request(self, req_msg: dict):
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
            protocol = req_msg.get('protocol')
            if protocol is None:
                # ignore invalid
                app.logger.debug("Websocket recieved: invalid, no protocol")
                return

            ref_no = req_msg.get('ref_no')
            if ref_no is None:
                # ignore invalid
                app.logger.debug("Websocket recieved: invalid, no ref_no")
                return

            request = req_msg.get('request')

            await asyncio.sleep(2)

            if protocol == 'echo':
                rep_msg = {
                    'protocol': protocol,
                    'ref_no': ref_no,
                    'reply': request,
                }
                await self.ws.send(json.dumps(rep_msg))
            elif protocol == 'a':
                reply = await self.komsession.raw_request(request.encode('utf-8'))
                rep_msg = {
                    'protocol': protocol,
                    'ref_no': ref_no,
                    'reply': reply.decode('utf-8')
                }
                await self.ws.send(json.dumps(rep_msg))
            else:
                # ignore invalid
                app.logger.debug(f"Websocket recieved: invalid, unknown protocol: {protocol}")
                await self.send_error(ref_no, f"Unknown protocol: {protocol}")

        except Exception as e:
            app.logger.error("Error handling request: %s", e)
            await self.send_error(ref_no, str(e))


    async def send_error(self, ref_no: Optional[int], error: str):
        error_response = {
            'ref_no': ref_no,
            'error': error
        }
        await self.ws.send(json.dumps(error_response))


    async def handle_connection(self):
        """Main loop for handling the WebSocket connection"""
        try:
            while True:
                data = await self.ws.receive()
                app.logger.debug(f"Websocket received: {data!r}")

                try:
                    req_msg = json.loads(data)
                except json.JSONDecodeError:
                    app.logger.error(f"Failed to json decode {data!r}: {de}")
                    continue

                # Create a task for handling this request
                task = asyncio.create_task(self.handle_request(req_msg))

                # Store task with ref_no if we want to cancel it later
                if 'ref_no' in req_msg:
                    self.tasks[str(req_msg['ref_no'])] = task

                # Clean up completed tasks
                done_refs = [
                    ref for ref, task in self.tasks.items()
                    if task.done()
                ]
                for ref in done_refs:
                    del self.tasks[ref]

        except asyncio.CancelledError:
            # Cancel all pending tasks when the connection is closed
            for task in self.tasks.values():
                task.cancel()
            raise
        finally:
            # Clean up any resources if needed
            pass


@app.websocket('/websocket')
async def ws_new():
    app.logger.debug("Websocket connected")

    g.connection_id = _get_connection_id_from_websocket()
    g.ksession = _get_komsession(g.connection_id)

    if g.ksession is None:
        return error_response(403, error_msg='Invalid connection id')

    try:
        connection = WebSocketConnection(websocket, g.ksession)
        await connection.handle_connection()
    except asyncio.CancelledError as e:
        # disconnect
        app.logger.debug("Websocket disconnected")
        raise
    except Exception as e:
        app.logger.exception("WebSocket error: %s", e)
        await websocket.close(1000)
    finally:
        # if something needs to be cleaned up
        pass
