import json

from orbitals_table import OrbitalsTable, GameState

class OrbitalsTableManager():
    def __init__(self, connections=None,
                 player_limit=8,
                 time_limit=1.0,
                 word_bag=None):
        if not connections:
            self._connections = dict()
        else:
            self._connections = connections
        self._table = OrbitalsTable(player_limit=player_limit,
                            time_limit=time_limit,
                            callback=self.dataOut)

    def playerLeft(self, sender):
        name = self._connections[sender]
        self._table.playerLeaves(name)
        del self._connections[sender]
        self.broadcast(f"{name} has left")

    def playerMessage(self, sender, packet):
        data = json.loads(packet)
        if sender not in self._connections.keys():
            self._connections[sender] = ""

            if data["type"] == "name-request":
                resp = self._table.playerJoins(data["name"])
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()

                sender.new_data(json.dumps(response))
                
                if resp == "name accepted":
                    self._connections[sender] = data["name"]
                    self.broadcast(f'{data["name"]} has joined the game')
            elif data["type"] == "connection":
                response = dict()
                response["type"] = "msg"
                response["msg"] = "provide name"
                sender.new_data(json.dumps(response))
        else:
            if data["type"] == "name-request":
                resp = self._table.playerJoins(data["name"])
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()

                sender.new_data(json.dumps(response))
                
                if resp == "name accepted":
                    self._connections[sender] = data["name"]
                    self.broadcast(f'{data["name"]} has joined the game')
            elif data["type"] == "team-request":
                name = self._connections[sender]
                resp = self._table.teamRequest(name, data["team"])
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()

                sender.new_data(json.dumps(response))
                
                if resp == "team accepted":
                    self._connections[sender] = name
                    self.broadcast(f'{name} has joined the {data["team"]} team')
            elif data["type"] == "role-request":
                name = self._connections[sender]
                resp = self._table.roleRequest(name, data["role"])
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                sender.new_data(json.dumps(response))
                
                if resp == "role accepted":
                    self._connections[sender] = name
                    self.broadcast(f'{name} is now a {data["role"]}')
            elif data["type"] == "start-request":
                name = self._connections[sender]
                resp = self._table.startRequest(name)

                response = dict()
                response["type"] = "status"
                response["status"] = self._table.status()

                if self._table.status()["game_state"] == "WAITING-CLUE":
                    self.broadcast(f'game has started')
            elif data["type"] == "new-clue":
                name = self._connections[sender]
                resp = self._table.newClue(name, data["clue"],int(data["count"]))
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                sender.new_data(json.dumps(response))
                if self._table.status()["game_state"] == "WAITING-APPROVAL":
                    self.broadcast(f'new clue has been submitted')
            elif data["type"] == "clue-approved":
                name = self._connections[sender]
                resp = self._table.clueResponse(name, True)
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                sender.new_data(json.dumps(response))
                if self._table.status()["game_state"] == "WAITING-GUESS":
                    self.broadcast(f'clue has been approved')
            elif data["type"] == "clue-rejected":
                name = self._connections[sender]
                resp = self._table.clueResponse(name, False)
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                sender.new_data(json.dumps(response))

                if self._table.status()["game_state"] == "WAITING-CLUE":
                    self.broadcast(f'clue has been approved')
            elif data["type"] == "new-guess":
                name = self._connections[sender]
                resp = self._table.newGuess(name, data["guess"])
                response = dict()
                response["type"] = "msg"
                response["msg"] = resp
                response["status"] = self._table.status()
                sender.new_data(json.dumps(response))

                self.broadcast(f'guess has been submitted')
            
            elif data["type"] == "status-request":
                response = dict()
                response["type"] = "status"
                response["status"] = self._table.status()
                sender.new_data(json.dumps(response))


    def broadcast(self, message):
        msg = dict()
        msg["type"] = "broadcast"
        msg["status"] = self._table.status()
        msg["msg"] = message
        for player in self._connections.keys():
            # print(f"Updating msg queue in {player.name()}")
            player.new_data(json.dumps(msg))

    # def dataIn(self, packet=None):
    #     data = json.loads(packet)
    #     response = dict()
    #     if data["type"] == "connection":
    #         response["type"] = "msg"
    #         response["msg"] = "provide name"
    #     elif data["type"] == "player-left":
    #         self._table.playerLeaves(data["name"])
    #     elif data["type"] == "name-request":
    #         response["type"] = "msg"
    #         response["msg"] = self._table.playerJoins(data["name"])
    #     elif data["type"] == "team-request":
    #         response["type"] = "msg"
    #         response["msg"] = self._table.teamRequest(data["name"], data["team"])
    #     elif data["type"] == "role-request":
    #         response["type"] = "msg"
    #         response["msg"] = self._table.roleRequest(data["name"], data["role"])
    #     elif data["type"] == "start-request":
    #         response["type"] = "msg"
    #         response["msg"] = self._table.startRequest(data["name"])
    #     elif data["type"] == "new-clue":
    #         response["msg"] = self._table.newClue(data["name"], data["clue"], int(data["count"]))
    #     elif data["type"] == "clue-response":
    #         response["msg"] = self._table.clueResponse(data["name"], bool(data["response"]))
    #     elif data["type"] == "new-guess":
    #         response["msg"] = self._table.newGuess(data["name"], data["guess"])
    #     elif data["type"] == "control":
    #         if data["cmd"] == "stop-timer":
    #             self._table.stopTimer()
    #     else:
    #         response["type"] = "msg"
    #         response["msg"] = "message not recognized"
    #     response["status"] = self._table.status()
    #     return json.dumps(response)

    def dataOut(self, message):
        pass

