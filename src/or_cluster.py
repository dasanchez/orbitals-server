"""
or_cluster.py
Orbitals cluster module
Tracks quadrants and routes player packets accordingly.
"""
import json
from pprint import pprint
from or_sector import OrbitalsSector

sectorNames = ['α / ALPHA', 'β / BETA', 'γ / GAMMA', 'δ / DELTA',
               'φ / PHI', 'χ / CHI', 'ψ / PSI', 'ω / OMEGA']

class OrbitalsCluster:
    """ Top level class """

    def __init__(self, sectorCount = 4):
        # initialize set of quadrants
        self._sectors = set()
        # self._users = set()
        self._userSectors = dict()
        self._sectorDict = dict()
        self.populateSectors(sectorCount)
        
    def populateSectors(self, count):
        # populate quadrant set
        for i in range(count):
            newSector = OrbitalsSector(wordCount=16,
                                           turnTimeout=30,
                                           sector=sectorNames[i])
            self._sectors.add(newSector)
            self._sectorDict[sectorNames[i]] = newSector
    
    def printSectors(self):
        for sector in self._sectors:
            print(f"{sector.getSectorDetails()}")

    def getClusterStatus(self):
        # returns a dict with all the quadrants and their players
        clusterStatus = []
        for s in self._sectors:
            clusterStatus.append(s.getSectorDetails())
        return clusterStatus

    # def newPlayer(self, websocket):
        # send quadrant data to new player

    async def newConnection(self, websocket):
        """ register player """
        print("New user connected")

        # self._users.add(websocket)
        self._userSectors[websocket] = None
        # issue cluster info
        sectors = sorted(list(self.getClusterStatus()), key=lambda k:k['name'])
        packet = {}
        packet['type'] = 'sectors'
        packet['sectors'] = sectors
        msg = json.dumps(packet)
        await websocket.send(msg)

    async def deleteConnection(self, websocket):
        """player has left:
        1. find out which orbital they belonged to
        2. send the signal to the relevant orbital
        """
        sector = self._userSectors[websocket]
        if sector:
            print(f"User is leaving sector {sector.getSectorDetails()['name']}.")
            await sector.deleteConnection(websocket)
            
        else:
            print("User did not belong to any sector.")

        self._userSectors.pop(websocket, None)
        await self.publishClusterStatus()
        # pprint(f"User sectors: {self._userSectors}")

    async def newMessage(self, websocket, data):
        """
        parse new message:
        1. if message asks to join a sector, handle in this class
        2. otherwise, find the sector the player belongs to and route accordingly
        """
        playerSector = self._userSectors[websocket]
        if playerSector is None:
            # player doesn't belong to a sector
            if data['type'] == 'join-sector':
                # get player to join the sector
                requestedSector = data['sector']
                sector = self._sectorDict[requestedSector]
                if sector:
                    await sector.newConnection(websocket)
                    self._userSectors[websocket] = sector
                    print(f"Player has joined sector {requestedSector}")
                    
        else:
            # player already belongs to a sector
            # TODO: what if the player wants to leave a sector?
            sector = self._userSectors[websocket]
            await sector.newMessage(websocket,data)

        if data['type'] == 'team-request' or data['type'] == 'source-request':
            await self.publishClusterStatus()

    async def publishClusterStatus(self):
        # publish update to all users with no sectors:
        sectors = sorted(list(self.getClusterStatus()), key=lambda k:k['name'])
        packet = {'type': 'sectors',
                  'sectors': sectors}
        msg = json.dumps(packet)
        for user in self._userSectors.keys():
            if not self._userSectors[user]:
                await user.send(msg)