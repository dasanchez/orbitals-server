import pytest
from collections import Counter
from orbitals_table import OrbitalsTable, GameState
from orbitals_board import OrbitalsBoard

def test_random_tileset():
    board = OrbitalsBoard('assets/or_words.txt')
    board.generateTiles()
    tiles1 = board.tiles()
    board.generateTiles()
    tiles2 = board.tiles()
    assert tiles1 != tiles2

def test_random_tileset_teams():
    board = OrbitalsBoard('assets/or_words.txt')
    board.generateTiles()
    tiles = board._tiles
    tile_counter = Counter([tile[0] for tile in tiles.values()])
    assert abs(tile_counter['blue'] - tile_counter['orange']) == 1
