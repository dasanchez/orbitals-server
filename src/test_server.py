import argparse
import asyncio
import websockets
import or_server

def test_server_connection(port = 9001):
    # set up server
    args = argparse.Namespace()
    args.port = port
    args.test = True
    args.secure = False
    or_server.main(args)

    # create client
    uri = "ws://localhost:" + port

