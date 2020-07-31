"""
Orbitals WebSockets Server
"""
import argparse
import functools
from pprint import pprint
import asyncio
import json
import ssl
import websockets
from or_cluster import OrbitalsCluster

orCluster = OrbitalsCluster(sectorCount=8)

def main(args):
    """ starts the game loop """
    print("State set to 'waiting-players'")
    print("Initialized sectors:")
    print("Sectors:")
    pprint(orCluster.getClusterStatus())

    print(args)
    port = args.port
    print(f"Opening websocket server on port {port}...")
    
    bound_handler = functools.partial(handler)
    # Set up async routines
    loop = asyncio.get_event_loop()

    if args.secure:
        chainFileName = args.secure[0]
        keyFileName = args.secure[1]
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(chainFileName, keyFileName)
        start_server = websockets.serve(bound_handler, '0.0.0.0', port, ssl=ssl_context)
        try:
            loop.run_until_complete(start_server)
            loop.run_forever()
        finally:
            loop.close()
    else:
        start_server = websockets.serve(bound_handler, '0.0.0.0', port)
        try:
            loop.run_until_complete(start_server)
            loop.run_forever()
        finally:
            loop.close()

async def handle_message(websocket, data):
    """ handles incoming message from players """
    await orCluster.newMessage(websocket, data)

async def handler(websocket, _):
    """ register(websocket) sends user_event() to websocket """
    await orCluster.newConnection(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            print(data)
            await handle_message(websocket, data)
    finally:
        # pass
        await orCluster.deleteConnection(websocket)

if __name__ == "__main__":
    # program entry point
    # validate input
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port",
                        help="specify the port to listen on",
                        nargs='?',
                        type=int,
                        default=9001)
    parser.add_argument("-s", "--secure",
                        help="use secure websockets: [full-chain] [private-key]",
                        nargs=2,
                        default=False)
    parser.add_argument("-t", "--test",
                        help="use test deck",
                        default=False)
    parser.add_argument("-v", "--verbose",
                        help="show progress", action="store_true")
    para = parser.parse_args()
    main(para)
    