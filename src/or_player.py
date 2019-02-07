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
    def __init__(self, name):
        self._name = name
        self._team = 'N'
        self._source = False
        self._ready = False
        self._replay = False
        self._websocket = None

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

    def setSource(self):
        self._source = True

    def isSource(self):
        return self._source

    def setReady(self, ready):
        self._ready = ready

    def isReady(self):
        return self._ready

    def setReplay(self, replay):
        self._replay = replay
        
    def wantsReplay(self):
        return self._replay