"""
or_players.py
Handles all players at the table
"""
from or_player import OrbitalsPlayer

class OrbitalsPlayers:
    """ Top level class """
    def __init__(self):
        self._players = set()
        self._enoughPlayers = False
        self._blueRoot = False
        self._orangeRoot = False
        self._blueTeam = 0
        self._orangeTeam = 0

    def getPlayers(self):
        """ Returns set of or_player objects """
        return self._players

    def getPlayerData(self):
        """
        Returns list of player data dicts: name, team, source, and ready
        """
        playerData = []
        for player in self._players:
            playerData.append({'name': player.getName(),
                               'team': player.getTeam(),
                               'src': player.isSource(),
                               'ready': player.isReady()})
        return playerData

    def getPlayersNames(self):
        """ Returns a set of player names """
        return {player.getName() for player in self._players}

    def getOrangeTeamCount(self):
        return self._orangeTeam

    def getBlueTeamCount(self):
        return self._blueTeam

    def nameExists(self, name):
        """ Returns True if name is already taken, False if it isn't """
        names = {player.getName() for player in self._players}
        return name in names

    def addPlayer(self, name, websocket):
        """
        If the requested name isn't taken yet:
            - Adds new or_player to _players list
            - Returns True
        if the name is already taken: returns False
        """
        if not name:
            return False, 'Name is blank'

        if not self.nameExists(name):
            newPlayer = OrbitalsPlayer(name)
            newPlayer.setWebSocket(websocket)
            self._players.add(newPlayer)
            return True, 'added'
        return False, 'Name exists'

    def removePlayer(self, websocket):
        """
        Handles a player leaving the game:
        Removes the player from the _players list
        If there aren't enough players left:
        - set all players' ready flags to False
        - return False
        Otherwise return True
        """
        print(f"player {self.playerName(websocket)} has left.")
        retiredPlayer = None
        for player in self.getPlayers():
            if player.getWebSocket() == websocket:
                retiredPlayer = player
                break
        if retiredPlayer:
            self._players.remove(retiredPlayer)
            # del retiredPlayer

        if not self.enoughPlayers():
            for player in self.getPlayers():
                player.setReady(False)
            return False
        return True

    def enoughPlayers(self):
        """
        Returns true if there is at least one source and one player per team,
        false otherwise
        """
        self._blueRoot = False
        self._orangeRoot = False
        self._blueTeam = 0
        self._orangeTeam = 0
        oPlayers = bPlayers = oSource = bSource = False
        for player in self._players:
            if player.getTeam() == 'B':
                self._blueTeam += 1
                if player.isSource():
                    bSource = True
                    self._blueRoot = True
                else:
                    bPlayers = True
            elif player.getTeam() == 'O':
                self._orangeTeam += 1
                if player.isSource():
                    oSource = True
                    self._orangeRoot = True
                else:
                    oPlayers = True
        requiredList = [oPlayers, bPlayers, oSource, bSource]
        self._enoughPlayers = all(requiredList)
        return self._enoughPlayers

    def playerName(self, websocket):
        """
        Returns the name if a player object matches the websocket object
        """
        for player in self._players:
            if player.getWebSocket() == websocket:
                return player.getName()
        return None

    def haveBlueRoot(self):
        return self._blueRoot

    def haveOrangeRoot(self):
        return self._orangeRoot

    def playerId(self, websocket):
        """ Returns player object """
        for player in self._players:
            if player.getWebSocket() == websocket:
                return player
        return None

    def joinTeam(self, websocket, team):
        """
        Handles a player joining a team
        If there are enough players to start the game:
        - Return True
        Otherwise return False
        """
        print(f"{self.playerName(websocket)} has requested team {team}")
        # check if there are less than four players in the team
        if team == 'O':
            if self._orangeTeam < 4:
                self.playerId(websocket).setTeam(team)
            else:
                return False, 'Orange team is full'
        elif team == 'B':
            if self._blueTeam < 4:
                self.playerId(websocket).setTeam(team)
            else:
                return False, 'Blue team is full'
        self.enoughPlayers()
        return True, 'team-accepted'

    def getTeam(self, name):
        """ Returns the team the player belongs to """
        for player in self._players:
            if player.getName() == name:
                return player.getTeam()
        return False

    def requestSource(self, websocket):
        """
        If role is available:
        - Sets source flag to True for player
        If there are enough players, returns True
        Otherwise returns False
        """
        print(f"{self.playerName(websocket)} has requested source role")
        player = self.playerId(websocket)
        if self.sourceAvailable(player.getTeam()):
            player.setSource()
            self.enoughPlayers()
            return True, 'source-accepted'
        return False, 'Hub role not available'

    def sourceAvailable(self, team):
        """
        Returns True if source role is available for specified team
        """
        for player in self._players:
            if player.getTeam() == team and player.isSource():
                return False
        return True

    def requestStart(self, websocket):
        """
        Returns True if if both teams are ready to start
        Returns False otherwise
        """
        print(f"{self.playerName(websocket)} is ready to start")
        if self.enoughPlayers():
            if self.playerId(websocket).isSource():
                self.playerId(websocket).setReady(True)

            # are both players ready?
            readyCount = 0
            for player in self._players:
                if player.isSource() and player.isReady():
                    readyCount += 1
            print(f"Ready count: {readyCount}")
            if readyCount == 2:
                return True
        return False

    def requestReplay(self, websocket):
        """
        Handles requests to play again after game ends.
        Returns True if all players ready and resets their flags
        Returns False otherwise
        """
        readyPlayer = self.playerId(websocket)
        readyPlayer.setReplay(True)
        replayNow = True

        for player in self._players:
            if not player.wantsReplay():
                replayNow = False
                break

        if replayNow:
            # set status of all non-source players to non-ready
            for player in self._players:
                player.setReplay(False)
                player.setReady(False)
            return True

        return False
