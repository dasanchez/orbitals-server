"""
or_cluster.py
Orbitals cluster module
Tracks quadrants and routes player packets accordingly.
"""
import json
from pprint import pprint
from or_sector import OrbitalsSector

sectorNames = ['ALPHA', 'BETA', 'GAMMA', 'DELTA',
               'PHI', 'CHI', 'PSI', 'OMEGA']
sectorSymbols = ['α', 'β', 'γ', 'δ',
               'φ', 'χ', 'ψ', 'ω']

class OrbitalsCluster:
    """ Top level class """

    def __init__(self, sectorCount = 4):
        # initialize set of quadrants
        self._sectors = set()
        # self._users = set()
        self._userSectors = dict()
        self._sectorDict = dict()
        self._userNames = dict()
        self.populateSectors(sectorCount)
        
    def populateSectors(self, count):
        # populate quadrant set
        for i in range(count):
            newSector = OrbitalsSector(wordCount=16,
                                           turnTimeout=30,
                                           name=sectorNames[i],
                                           symbol=sectorSymbols[i])
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

        packet = {}
        packet['type'] = 'welcome'
        packet['prompt'] = 'Enter your name'
        # packet['type'] = 'sectors'
        # packet['sectors'] = sectors
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
        self._userNames.pop(websocket, None)
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
                    await sector.newPlayer(self._userNames[websocket], websocket)
                    self._userSectors[websocket] = sector
                    print(f"Player has joined sector {requestedSector}")
                else:
                    print(f"{requestedSector} does not exist")
            elif data['type'] == 'name-request':
                name = data['name']
                if not name:
                    # name is blank
                    response = 'Name is blank'
                    packet = {'type': 'response',
                              'msg': "name-not-accepted",
                              'reason': response}
                    msg = json.dumps(packet)
                    await websocket.send(msg)
                elif name in self._userNames.values():
                    # name is taken
                    response = 'Name exists'
                    packet = {'type': 'response',
                              'msg': "name-not-accepted",
                              'reason': response}
                    msg = json.dumps(packet)
                    await websocket.send(msg)
                else:
                    # name is OK
                    self._userNames[websocket] = name
                    packet = {'type': 'response', 'msg': "name-accepted", 'name': name}
                    packet['prompt'] = "Choose a sector"
                    sectors = sorted(list(self.getClusterStatus()), key=lambda k:k['symbol'])
                    packet['sectors'] = sectors
                    msg = json.dumps(packet)
                    await websocket.send(msg)
                    
        else:
            # player already belongs to a sector
            if data['type'] == 'leave-sector':
                # only capture one type of message: user leaving the sector
                print(f"User is leaving sector {playerSector.getSectorDetails()['name']}.")
                
                # notify the sector
                await playerSector.deleteConnection(websocket)

                # send message to user to notify they are sector-less
                sectors = sorted(list(self.getClusterStatus()), key=lambda k:k['symbol'])
                packet = {}
                packet['type'] = 'response'
                packet['msg'] = 'left-sector'
                packet['sectors'] = sectors
                packet['prompt'] = "Choose a sector"
                msg = json.dumps(packet)
                await websocket.send(msg)

                # remove user from dictionary and publish cluster status
                self._userSectors[websocket] = None
                await self.publishClusterStatus()
        
            else:
                # message gets a pass-through
                sector = self._userSectors[websocket]
                await sector.newMessage(websocket,data)

                if data['type'] == 'team-request' or data['type'] == 'hub-request':
                    await self.publishClusterStatus()

    async def publishClusterStatus(self):
        # publish update to all users with no sectors:
        sectors = sorted(list(self.getClusterStatus()), key=lambda k:k['symbol'])
        packet = {'type': 'sectors',
                  'sectors': sectors}
        msg = json.dumps(packet)
        for user in self._userSectors.keys():
            if not self._userSectors[user]:
                await user.send(msg)