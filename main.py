"""
NOTES

- The variable `s` is _always_ a tuple of my_piece_locations, and
  their_piece_locations
"""
from AlphaBetaPlayer import AlphaBetaPlayer
from RandomPlayer import RandomPlayer
from MCTSPlayer import MCTSPlayer
import time
import socket
import sys
from board import Board

INF = 1.0e100
CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]
CENTERS = [(3, 3), (3, 4), (4, 3), (4, 4)]
DANGERS = [(0, 1), (0, 6), (1, 0), (1, 1), (1, 6), (1, 7), (6, 0), (6, 1),
           (6, 6), (6, 7), (7, 1), (7, 6)]

G_EDGES = [(0, 2), (0, 3), (0, 4), (0, 5), (2, 0), (3, 0), (4, 0), (5, 0),
           (2, 7), (3, 7), (4, 7), (5, 7), (7, 2), (7, 3), (7, 4), (7, 5)]

NEIGHBORS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0),
             (1, 1)]

# ai_types = {"random": RandomPlayer, "MCTS":  MCTSPlayer, "alphabeta": AlphaBetaPlayer}

if sys.version_info.major == 2:
    range = xrange

    def iteritems_dict(x):
        return x.iteritems()
else:
    def iteritems_dict(x):
        return x.items()

def get_value(future):
    return future[0]


def printState(s):
    # INVERTS TO MATCH VISUAL
    pprint(s[::-1])


def compare(a, b):
    return (a > b) - (a < b)

class Simulator(object):
    def __init__(self, p1, p2, state=None):
        self.p1 = p1
        self.p2 = p2
        if state is None:
            self.board = Board()
            self.board.init()
        else:
            self.board = Board(state[0], state[1])

    # 100 moves is more than the max (64), so a whole game will be played
    def run_simulation(self, n_moves=100, disp=False):
        move = 0
        while move < n_moves:
            move += 1
            if self.board.is_over():
                break

            moves = self.board.get_moves()
            if self.board.player_turn == 1:
                action = self.p1.move(moves)
            else:
                action = self.p2.move(moves)

            self.board.do_action(self.board.spaces[action])

            if disp:
                print(self.board.p1_placed, self.board.p2_placed)
                print(self.board)

        return self.board.p1_placed, self.board.p2_placed

# python main.py [server_address] [ai_type] [player_number]
if __name__ == "__main__":

    if len(sys.argv) >= 3:
        print(('Number of arguments: ', len(sys.argv)))
        print(('Argument List: ', str(sys.argv)))
        print((str(sys.argv[1])))

        ai = sys.argv[2]

        me = int(sys.argv[3])
        you = 1 if me == 2 else 2

        arg = sys.argv[1]
        if ai == "random":
            player = RandomPlayer(me, you)
        elif ai == "alphabeta":
            player = AlphaBetaPlayer(me, you)
        elif ai =="MCTS":
            player = MCTSPlayer(me, you)
        player.play_game(arg)

        # import cProfile
        # cProfile.run('player.play_game("{}")'.format(arg))
