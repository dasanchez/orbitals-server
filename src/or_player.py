"""
or_player.py
Orbitals player class
Tracks:
- name
- team
- role
- readiness
- replay status
- websocket
"""

class OrbitalsPlayer:
    """ Handles player properties """
    def __init__(self, name, websocket=None):
        self._name = name
        self._sector = None
        self._team = 'N'
        self._hub = False
        self._ready = False
        self._replay = False
        self._websocket = websocket

    def setSector(self, sector):
        self._sector = sector

    def getSector(self):
        return self._sector

    def setWebSocket(self, websocket):
        self._websocket = websocket

    def getWebSocket(self):
        return self._websocket

    def setName(self, newName):
        self._name = newName

    def getName(self):
        return self._name

    def setTeam(self, newTeam):
        if newTeam == 'O' or newTeam == 'B':
            self._team = newTeam
        else:
            self._team = 'N'

    def getTeam(self):
        return self._team

    def setHub(self, role = True):
        self._hub = role

    def isHub(self):
        return self._hub

    def setReady(self, ready):
        self._ready = ready

    def isReady(self):
        return self._ready

    def setReplay(self, replay):
        self._replay = replay
        
    def wantsReplay(self):
        return self._replay