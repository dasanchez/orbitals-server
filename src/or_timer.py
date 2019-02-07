"""
or_timer.py
Timer class
"""

class OrbitalsTimer:
    def __init__(self, seconds):
        self._active = True
        self._timeout = seconds
        self._timeRemaining = 0
    
    def getTimout(self):
        return self._timeout

    def getTime(self):
        return self._timeRemaining

    def start(self, seconds = None):
        if seconds is None:
            seconds = self._timeout
        self._timeRemaining = seconds
        self._active = True

    def stop(self):
        self._active = False
        self._timeRemaining = 0
    
    def isActive(self):
        return self._active

    def tick(self):
        if self._timeRemaining > 0:
            self._timeRemaining -= 1
