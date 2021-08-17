"""
orbitals_board.py
Orbitals board engine
Manages tile board and winner
"""

import random

class OrbitalsBoard:
    """ Top level class """

    def __init__(self, word_bag=None, tile_count: int=16):
        self._tiles = dict()
        self._test_game = False
        if not word_bag:
            self._test_game = True
        else:
            self._word_file = word_bag
        self._tile_count = tile_count
        self._first_turn = ''
        
    def readWords(self):
        """
        Reads words form a text file and assigns them to _fullDeck set
        """
        orWordFile = open(self._word_file, 'r')
        self._fullDeck = {line.strip() for line in orWordFile.readlines()}

    def generateTiles(self):
        #TODO: actually generate new tiles every time
        if self._test_game:
            self._tiles = {
                'APPLE': ['blue', False],
                'BOMB': ['blue', False],
                'CROWN': ['blue', False],
                'DAD': ['blue', False],
                'EASTER': ['blue', False],
                'FLAG': ['blue', False],
                'GIANT': ['blue', False],
                'HOME': ['blue', False],
                'INDIA': ['orange', False],
                'JUICE': ['orange', False],
                'KILOGRAM': ['orange', False],
                'LION': ['orange', False],
                'MEXICO': ['orange', False],
                'NIGHT': ['orange', False],
                'OPERA': ['orange', False],
                'PASTA': ['neutral', False]
            }
            # return team with the higher word count
            self._first_turn = 'blue'
        else:
            self.readWords()
            self._tiles = dict()
            # get a shuffled set of tiles
            tempDeck = list(self._fullDeck)
            for _ in range(self._tile_count):
                pick = random.randint(0, len(tempDeck)-1)
                self._tiles[tempDeck[pick]] = ['neutral', False]
                tempDeck.remove(tempDeck[pick])

            # flip a coin to decide who goes first
            first = random.randint(0, 1)
            if first:
                blue = True
                self._firstTurn = 'blue'
            else:
                blue = False
                self._firstTurn = 'orange'

            # assign teams
            # tempDeck will be consumed
            tempDeck = list(self._tiles.keys())

            for _ in range(len(self._tiles)):
                pick = random.randint(0, len(tempDeck)-1)
                # Stop assigning keys when there are three words left,
                # we want three neutral words
                if len(tempDeck) > 3:
                    if blue:
                        self._tiles[tempDeck[pick]] = ['blue', False]
                    else:
                        self._tiles[tempDeck[pick]] = ['orange', False]
                blue = not blue
                tempDeck.remove(tempDeck[pick])

    def flipTile(self, tile: str):
        self._tiles[tile][1] = True
        
    def tiles(self):
        # return dictionary:
        # key: word
        # value: the team that owns this word, or blank
        exposed_tiles = self._tiles.copy()
        for key in exposed_tiles.keys():
            if exposed_tiles[key][1]:
                exposed_tiles[key] = exposed_tiles[key][0]
            else:
                exposed_tiles[key] = ''
        return exposed_tiles

    def tiles_left(self, *, team: str):
        return len([tile for tile in self._tiles.values() if tile[0] == team and tile[1] == False])

    def firstTurn(self):
        return self._first_turn

    def winner(self):
        # check if all blue tiles have been exposed
        if all([tile[1] for tile in self._tiles.values() if tile[0] == 'blue']):
            return 'blue'
        elif all([tile[1] for tile in self._tiles.values() if tile[0] == 'orange']):
            return 'orange'
        else:
            return None