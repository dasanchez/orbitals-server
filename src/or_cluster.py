"""
or_cluster.py
Orbitals cluster module
Tracks quadrants and routes player packets accordingly.
"""
import json
from or_quadrant import OrbitalsQuadrant

quadrantNames = ['ALPHA', 'BETA', 'GAMMA', 'DELTA']

class OrbitalsCluster:
    """ Top level class """

    def __init__(self, quadrantCount = 4):
        # initialize set of quadrants
        self._quadrants = set()
        self._users = set()
        self._userQuadrants = dict()
        self.populateQuadrants(quadrantCount)
        
    def populateQuadrants(self, count):
        # populate quadrant set
        for i in range(count):
            newQuadrant = OrbitalsQuadrant(wordCount=16,
                                           turnTimeout=30,
                                           quadrant=quadrantNames[i])
            self._quadrants.add(newQuadrant)
    
    def printQuadrants(self):
        for quadrant in self._quadrants:
            print(f"{quadrant.getQuadrantDetails()}")

    def getClusterStatus(self):
        # returns a dict with all the quadrants and their players
        clusterStatus = []
        for q in self._quadrants:
            clusterStatus.append(q.getQuadrantDetails())
        return clusterStatus

    # def newPlayer(self, websocket):
        # send quadrant data to new player

    async def newConnection(self, websocket):
        """ register player """
        print("New user connected")

        self._users.add(websocket)
        self._userQuadrants[websocket] = None
        # issue cluster info
        packet = sorted(list(self.getClusterStatus()), key=lambda k:k['name'])
                #   'clusters': {
                      
                #   },
        msg = json.dumps(packet)
        await websocket.send(msg)
        # issue list of players
        # await orbComms.publishPlayers(self._players.getPlayerData(),
                                    #   self._players.enoughPlayers(), self._users)

    async def deleteConnection(self, websocket):
        """player has left:
        1. find out which orbital they belonged to
        2. send the signal to the relevant orbital
        """

        if self._userQuadrants[websocket]:
            q = self._userQuadrants[websocket]
            print(f"User belonged to {q.getQuadrantDetails()['name']} quadrant")
        else:
            print("User did not belong to any quadrant.")