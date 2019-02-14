"""
or_cluster.py
Orbitals cluster module
Tracks quadrants and routes player packets accordingly.
"""
from or_quadrant import OrbitalsQuadrant

quadrantNames = ['ALPHA', 'BETA', 'GAMMA', 'DELTA']

class OrbitalsCluster:
    """ Top level class """

    def __init__(self, quadrantCount = 4):
        # initialize set of quadrants
        self._quadrants = set()
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

    # def newPlayer(self, websocket):
        # send quadrant data to new player
