import argparse
import asyncio
import websockets
import json
import pytest
from wserver import WServer
from or_cluster import OrbitalsCluster

# from or_server import OrbitalsServer
# import server_responses as sr

uri = "ws://localhost:9001"

# @pytest.fixture(scope="module")
# def event_loop():
    # loop = asyncio.get_event_loop()
#     test_server = WServer()
#     loop.create_task(test_server.start_server(wss=False, port=9001))
    # yield loop
#     # loop.close()

# @pytest.mark.asyncio
# async def test_client_connect():
#     async with websockets.connect(uri) as websocket:
#         # greeting = await websocket.recv()
#         # resp
#         pass

# @pytest.mark.asyncio
# async def test_multiple_clients(quantity=128):
#     clients = list()
#     for _ in range(quantity):
#         new_client = await websockets.connect(uri)
#         clients.append(new_client)
#     for client in clients:
#         client.close()

sector_quantity = 1

def cluster_message(payload):
    print()
    print(json.dumps(payload, indent=3))

@pytest.fixture
def create_cluster(sectors=sector_quantity):
    cluster = OrbitalsCluster(sectorCount=sectors, callback=cluster_message)
    yield cluster

def test_sector_count(create_cluster):
    cluster = create_cluster
    assert len(cluster.getClusterStatus()) == sector_quantity

def test_cluster_new_player(create_cluster):
    cluster = create_cluster
    response = cluster.newPlayer(name="Anna")
    assert response

    response = cluster.newPlayer(name="")
    assert response == "please enter a valid name"

    response = cluster.newPlayer(name="Anna")
    assert response == "please enter a different name"

def test_cluster_player_leaves(create_cluster):
    cluster = create_cluster
    cluster.newPlayer("Anna")

    cluster.playerLeaves("Anna")

def test_cluster_sector_request(create_cluster):
    cluster = create_cluster
    cluster.newPlayer(name="Anna")
    response = cluster.playerMessage("Anna", {"type":"join-sector", "sector": "ALPHA"})
    print(response)
    assert response["msg"] == "joined-sector"

# @pytest.mark.asyncio
# async def test_client_connect():
#    async with websockets.connect(uri) as websocket:
#         player_one_name = 'P1'
#         greeting = await websocket.recv()
#         resp = json.loads(greeting)
        
#         assert(resp == sr.CONN_RESPONSE_OK)

#         name_req = {'type': 'name-request', 'name':player_one_name}
#         await websocket.send(json.dumps(name_req))
#         response = await websocket.recv()
#         resp = json.loads(response)
#         name_accepted = sr.NAME_RESPONSE_OK
#         name_accepted['name'] = player_one_name

#         assert(resp == name_accepted)



# @pytest.mark.asyncio
# async def test_connect_multiple_clients():
#     clients = await connect_multiple_clients(32)
#     print("First response: ", await clients[0].recv())
#     name_req = {'type': 'name-request', 'name':'first'}

#     await clients[0].send(json.dumps(name_req))
#     response = await clients[0].recv()
    
#     name_ok = sr.NAME_RESPONSE_OK
#     name_ok['name'] = 'first'
#     assert(name_ok == json.loads(response))

#     print("Last client response: ", await clients[-1].recv())
#     name_req = {'type': 'name-request', 'name':'last'}
#     await clients[-1].send(json.dumps(name_req))
#     response = await clients[-1].recv()

#     name_ok = sr.NAME_RESPONSE_OK
#     name_ok['name'] = 'last'
#     assert(name_ok == json.loads(response))

#     for client in clients:
#         await client.close()
    
# @pytest.mark.asyncio
# async def test_join_sector_request():
#     # connection
#     ws = await websockets.connect(uri)
#     await ws.recv()

#     # name request
#     name_req = {'type': 'name-request', 'name':'P1'}
#     await ws.send(json.dumps(name_req))
#     response = await ws.recv()

#     # join sector request
#     sector_req = {'type': 'join-sector', 'sector':'ALPHA'}
#     await ws.send(json.dumps(sector_req))
#     response = await ws.recv()

#     assert(sr.SECTOR_RESPONSE_OK == json.loads(response))

#     await ws.close()

# @pytest.mark.asyncio
# async def test_leave_sector_request():
#     # connection
#     ws = await websockets.connect(uri)
#     await ws.recv()

#     # name request
#     name_req = {'type': 'name-request', 'name':'P1'}
#     await ws.send(json.dumps(name_req))
#     response = await ws.recv()

#     # join sector request
#     sector_req = {'type': 'join-sector', 'sector':'ALPHA'}
#     await ws.send(json.dumps(sector_req))
#     response = await ws.recv() # joined ok
#     print("> ", response)
#     response = await ws.recv() # state
#     print("> ", response) 
#     response = await ws.recv() # players
#     print("> ", response) 
#     response = await ws.recv() # joined sector broadcast
#     print("> ", response) 
    
#     # leave sector request
#     leave_req = {'type': 'leave-sector'}
#     await ws.send(json.dumps(leave_req))
#     response = await ws.recv()

#     print(">", response)
#     assert(sr.LEAVE_SECTOR_RESPONSE_OK == json.loads(response))

#     await ws.close()

    