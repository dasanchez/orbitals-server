import json
import asyncio

from orbitals_table import OrbitalsTable, GameState

class OrbitalsTableManager():
    def __init__(self, connections=None,
                 player_limit=8,
                #  time_limit=1.0,
                 word_bag=None,
                 callback=None):
        if not connections:
            self._connections = dict()
        else:
            self._connections = connections
        self._table = OrbitalsTable(player_limit=player_limit,
                            # time_limit=time_limit,
                            callback=self.tableMessage)
        if callback:
            self._callback = callback
        else:
            self._callback = None

    async def playerLeft(self, sender):
        if sender in self._connections.keys():
            name = self._connections[sender]
            self._table.playerLeaves(name)
            del self._connections[sender]
            await self.broadcast(f"{name} has left")

    async def playerMessage(self, sender, packet):
        data = json.loads(packet)
        if sender not in self._connections.keys():
            # self._connections[sender] = ""

            if data["type"] == "name-request":
                resp = self._table.playerJoins(data["name"])
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                response["name"] = data["name"]

                await sender.send(json.dumps(response))
                
                if resp == "name accepted":
                    self._connections[sender] = data["name"]
                    await self.broadcast(f'{data["name"]} has joined the game')
            elif data["type"] == "connection":
                response = dict()
                response["type"] = "msg"
                response["msg"] = "provide name"
                await sender.send(json.dumps(response))
        else:
            if data["type"] == "team-request":
                name = self._connections[sender]
                resp = self._table.teamRequest(name, data["team"])
                # print(f"{name} is requesting team {data['team']}")
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                response["team"] = data["team"]
                response["role"] = self._table.playerRole(name)
                await sender.send(json.dumps(response))
                
                if resp == "team accepted":
                    self._connections[sender] = name
                    await self.broadcast(f'{name} has joined the {data["team"]} team')
            elif data["type"] == "role-request":
                name = self._connections[sender]
                resp = self._table.roleRequest(name, data["role"])
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                response["role"] = data["role"]
                await sender.send(json.dumps(response))
                
                if resp == "role accepted":
                    self._connections[sender] = name
                    await self.broadcast(f'{name} is now a {data["role"]}')
            elif data["type"] == "start-request":
                name = self._connections[sender]
                resp = self._table.startRequest(name)

                response = dict()
                response["type"] = "status"
                response["status"] = self._table.status()
                # await sender.send(json.dumps(response))

                if self._table.status()["game_state"] == "WAITING_CLUE":
                    await self.broadcast(f'game has started')
                elif self._table.status()["game_state"] == "WAITING_START":
                    await self.broadcast(f"{name} has requested start")
            elif data["type"] == "new-clue":
                name = self._connections[sender]
                resp = self._table.newClue(name, data["clue"],int(data["count"]))
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                await sender.send(json.dumps(response))
                if self._table.status()["game_state"] == "WAITING_APPROVAL":
                    await self.broadcast(f'new clue has been submitted')
            elif data["type"] == "clue-approved":
                name = self._connections[sender]
                resp = self._table.clueResponse(name, True)
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                await sender.send(json.dumps(response))
                if self._table.status()["game_state"] == "WAITING_GUESS":
                    await self.broadcast(f'clue has been approved')
            elif data["type"] == "clue-rejected":
                name = self._connections[sender]
                resp = self._table.clueResponse(name, False)
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                await sender.send(json.dumps(response))

                if self._table.status()["game_state"] == "WAITING_CLUE":
                    await self.broadcast(f'clue has been approved')
            elif data["type"] == "new-guess":
                name = self._connections[sender]
                resp = self._table.newGuess(name, data["guess"])
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                await sender.send(json.dumps(response))

                await self.broadcast(f'guess has been submitted')
            elif data["type"] == "end-turn":
                name = self._connections[sender]
                resp = self._table.endTurn(name)
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                await sender.send(json.dumps(response))
                await self.broadcast(f'turn has ended')
            elif data["type"] == "replay-request":
                name = self._connections[sender]
                resp = self._table.replayRequest(name)
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                await sender.send(json.dumps(response))
                if self._table.status()["game_state"] == "WAITING_START":
                    await self.broadcast(f'all players are ready to play again')
                else:
                    await self.broadcast(f"{name} is ready to play again")
            elif data["type"] == "status-request":
                response = dict()
                response["type"] = "status"
                response["status"] = self._table.status()
                await sender.send(json.dumps(response))

    async def broadcast(self, message):
        msg = dict()
        msg["type"] = "broadcast"
        msg["status"] = self._table.status()
        msg["msg"] = message
        for player in self._connections.keys():
            if (msg["status"]["game_state"] == "WAITING_APPROVAL" and self._connections[player] == self._table.getApprover())\
                or msg["status"]["game_state"] == "WAITING_GUESS":
                hubmsg = msg.copy()
                hubmsg["status"]["clue"] = self._table.currentClue()
                hubmsg["status"]["guesses_left"] = self._table.guessesLeft()
                await player.send(json.dumps(hubmsg))
            else: 
                await player.send(json.dumps(msg))
        if self._callback:
            self._callback(msg)

    # async def tick(self, time_left):
    #     msg = dict()
    #     msg["type"] = "tick"
    #     msg["time_left"] = time_left
    #     for player in self._connections.keys():
    #         await player.send(json.dumps(msg))
    #     if self._callback:
    #         self._callback(msg)

    def tableMessage(self, message):
        if message[0] == "timeout":
            asyncio.run(self.broadcast("timeout"))
        # elif message[0] == "tick":
            # asyncio.run(self.tick(message[1]))