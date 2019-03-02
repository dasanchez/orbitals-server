"""
or_words.py
Orbitals words class
"""
import random

class OrbitalsWords:
    """ Provides the game words """
    def __init__(self, wordCount):
        self._fullDeck = set()
        self._orbWords = dict()
        self._openedWords = dict()
        self._wordCount = wordCount
        self._oWordsLeft = 0
        self._bWordsLeft = 0
        self._firstTurn = ''
        self.readWords()

    def readWords(self):
        """
        Reads words form a text file and assigns them to _fullDeck set
        """
        orWordFile = open('assets/or_words.txt', 'r')
        self._fullDeck = {line.strip() for line in orWordFile.readlines()}

    def shuffleDeck(self):
        """ Generate new set of words """
        self._orbWords.clear()
        self._openedWords.clear()

        # get a shuffled deck
        tempDeck = list(self._fullDeck)
        for _ in range(self._wordCount):
            print(f"deck has {len(tempDeck)} words")
            pick = random.randint(0, len(tempDeck)-1)
            print(f"pick: {pick}")
            self._orbWords[tempDeck[pick]] = 'N'
            self._openedWords[tempDeck[pick]] = '-'
            tempDeck.remove(tempDeck[pick])

    def assignKeys(self):
        """
        Randomly assign teams to words
        """
        tempDeck = list(self._orbWords.keys())

        # Flip a coin to decide who goes first
        first = random.randint(0, 1)
        if first:
            blue = True
            self._firstTurn = 'B'
        else:
            blue = False
            self._firstTurn = 'O'

        for _ in range(len(self._orbWords)):
            pick = random.randint(0, len(tempDeck)-1)
            # Stop assigning keys when there are three words left
            if len(tempDeck) > 3:
                if blue:
                    self._orbWords[tempDeck[pick]] = 'B'
                    self._bWordsLeft += 1
                else:
                    self._orbWords[tempDeck[pick]] = 'O'
                    self._oWordsLeft += 1
            blue = not blue
            tempDeck.remove(tempDeck[pick])

    def getFirstTurn(self):
        """ Returns starting team """
        return self._firstTurn

    def getWords(self):
        """
        Returns list of dictionaries with 'word' and 'team' keys
        Uses the _openedWords dictionary: includes guessed words
        """
        wordList = []
        for word, team in self._openedWords.items():
            wordList.append({'word': word, 'team': team})
        return wordList

    def getKeywords(self):
        """
        Returns list of dictionaries with 'word' and 'team' keys
        Uses the _orbWords dictionary
        """
        keyWordList = []
        for word, team in self._orbWords.items():
            keyWordList.append({'word': word, 'team': team})
        return keyWordList

    def getTeam(self, word):
        """ Returns the team the word belongs to """
        return self._orbWords[word]

    def reset(self):
        """
        Reset game status:
        - new words are read
        - turn is set to none
        - hint is cleared
        - words remaining by either team are cleared
        """
        self._orbWords = dict()
        self._openedWords = dict()
        self._bWordsLeft = 0
        self._oWordsLeft = 0

    def newGuess(self, guess, team):
        """ Process new guess """
        res = {"gameOver": False,
               "winner": '',
               "switch": False,
               "newGuess": False
              }
        # has this word been guessed before?
        if self._openedWords[guess] == '-':  # no
            res["newGuess"] = True
            self._openedWords[guess] = self._orbWords[guess]
            if self._orbWords[guess] == 'O':
                self._oWordsLeft -= 1
                if self._oWordsLeft == 0:
                    res["gameOver"] = True
                    res["winner"] = 'O'
            elif self._orbWords[guess] == 'B':
                self._bWordsLeft -= 1
                if self._bWordsLeft == 0:
                    res["gameOver"] = True
                    res["winner"] = 'B'

            if self._openedWords[guess] != team:
                # guesser guessed a word assigned to another team
                res["switch"] = True

        return res

    def wordsLeft(self, team):
        """ Returns number of words left to guess """
        if team == 'O':
            return self._oWordsLeft
        if team == 'B':
            return self._bWordsLeft
        return False

    def setSimulationWords(self):
        """ Utility function for development """
        self._orbWords = {'APPLE': 'O', 'BEER': 'O', 'CINNAMON': 'N',
                         'DICE': 'N', 'ELEPHANT': 'B', 'FARM': 'B',
                         'GRANDMA': 'O', 'HABIT': 'O', 'INDIA': 'O',
                         'JEEP': 'N', 'KARMA': 'B', 'LIME': 'B',
                         'MEXICO': 'O', 'NAAN': 'B', 'OWL': 'O',
                         'PERISCOPE': 'B'}
        self._openedWords = {'APPLE': '-', 'BEER': '-', 'CINNAMON': '-',
                             'DICE': '-', 'ELEPHANT': '-', 'FARM': '-',
                             'GRANDMA': '-', 'HABIT': '-', 'INDIA': '-',
                             'JEEP': '-', 'KARMA': '-', 'LIME': '-',
                             'MEXICO': '-', 'NAAN': '-', 'OWL': '-',
                             'PERISCOPE': '-'}
        self._bWordsLeft = 6
        self._oWordsLeft = 7
