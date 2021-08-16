import functools
import ssl
import websockets
# import asyncio

class WServer:
    def __init__(self, server_out=None):
        self.server_object = None
        self.bound_handler = functools.partial(self.handler)
        self.local_print = True
        if server_out != None:
            self.output = server_out
            self.local_print = False
        self.connections = list()

    async def start_server(self, wss=False, port=9090, chain=None, key=None):
        if wss:
            chain_filename = chain
            key_filename = key
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(chain_filename, key_filename)
            self.server_object = websockets.serve(self.bound_handler, '0.0.0.0', port=port, ssl=ssl_context)
        else:
            self.server_object = websockets.serve(self.bound_handler, '0.0.0.0', port=port)
        await self.server_object
        if self.server_object.ws_server.is_serving():
            self.data_out(data_type="status", payload="Server is running")

    async def stop_server(self):
        self.server_object.ws_server.close()
        await self.server_object.ws_server.wait_closed()
        if not self.server_object.ws_server.is_serving():
            self.data_out(data_type="status", payload="Server is not running")
        self.server_object = None

    async def handler(self, websocket, _):
        self.connections.append(websocket)
        # addr = websocket.remote_address[0]
        idx = self.connections.index(websocket)
        self.data_out("ev", f"Player {idx} has joined.")
        try:
            async for msg in websocket:
                self.data_out("msg", f"{idx}> {msg}")
        finally:
            self.connections.remove(websocket)
            del websocket
            self.data_out("ev", f"{idx} has left.")

    def data_out(self, data_type="msg", payload=""):
        packet_out = [data_type, payload]
        self.server_print(packet_out)

    async def broadcast(self, payload=""):
        for ws in self.connections:
            await ws.send(payload)

    def server_print(self, output):
        if self.local_print:
            print(output)
        else:
            self.output(output)
