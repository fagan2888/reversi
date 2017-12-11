"""
NOTES

- The variable `s` is _always_ a tuple of my_piece_locations, and
  their_piece_locations
"""
import time
import random
from pprint import pprint
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

if sys.version_info.major == 2:
    range = xrange

    def iteritems_dict(x):
        return x.iteritems()
else:
    def iteritems_dict(x):
        return x.items()


def print_futures(futures):
    for value_move in futures:
        print(value_move[1], ": ", value_move[0])


def get_value(future):
    return future[0]


def printState(s):
    # INVERTS TO MATCH VISUAL
    pprint(s[::-1])


def compare(a, b):
    return (a > b) - (a < b)


class Player(object):
    def __init__(self, me, you):
        self.me, self.you = me, you

        # handling the board
        self.board = Board()
        self.centers_bits = sum(self.board.spaces[i] for i in CENTERS)
        self.corners_bits = sum(self.board.spaces[i] for i in CORNERS)
        self.mine = 0
        self.foe = 0

    def get_valid_moves(self, s, player):

        if self.round < 4:
            centers_remaning_bits = self.centers_bits - s[0] - s[1]
            return self.board.bits_to_tuples(centers_remaning_bits)

        if player == self.me:
            return self.board.legal_actions(s[0], s[1])
        else:
            return self.board.legal_actions(s[1], s[0])

    def play_game(self, thehost):
        def init_client(thehost):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (thehost, 3333 + self.me)
            print((sys.stderr, 'starting up on %s port ', server_address))
            sock.connect(server_address)

            for ind, thing in enumerate(sock.recv(1024).decode().split("\n")):
                print("when init got {} and {}".format(ind, thing))

            return sock

        def read_message(sock):
            message = sock.recv(1024).decode().split("\n")
            turn = int(message[0])
            if (turn == -999):
                time.sleep(1)
                sys.exit()
            self.round = int(message[1])
            self.t1 = float(message[2])
            self.t2 = float(message[3])
            print("turn", turn)
            print("current time:", time.time())
            print("round:", self.round)
            print("t1:", self.t1)
            print("t2:", self.t2)
            count = 4
            self.mine = 0
            self.foe = 0
            for i in range(8):
                for j in range(8):
                    color = int(message[count])
                    if color == self.me:
                        self.mine += self.board.spaces[(i, j)]
                    elif color == self.you:
                        self.foe += self.board.spaces[(i, j)]
                    count += 1

            # update board
            self.board = Board(self.mine, self.foe)

            return turn

        # create a random number generator
        sock = init_client(thehost)
        while True:
            turn = read_message(sock)
            if turn == self.me:
                my_move = self.move(((self.mine, self.foe), turn))
                print("============")
                print("Round: ", self.round)
                # print("Valid moves: ", valid_moves)
                print("mine: ", self.mine)
                print("FOE: ", self.foe)
                print(self.board)
                # my_move = self.move(valid_moves)

                if my_move == CORNERS[0]:
                    G_EDGES.extend([(1, 0), (0, 1)])
                elif my_move == CORNERS[1]:
                    G_EDGES.extend([(1, 7), (0, 6)])
                elif my_move == CORNERS[2]:
                    G_EDGES.extend([(6, 0), (7, 1)])
                elif my_move == CORNERS[3]:
                    G_EDGES.extend([(6, 7), (7, 6)])

                msg = "{}\n{}\n".format(my_move[0], my_move[1])
                sock.send(msg.encode())


class RandomPlayer(Player):
    def __init__(self, me, you):
        super(RandomPlayer, self).__init__(me, you)

    def move(self, state):
        moves = self.get_valid_moves(state[0], state[1])
        return random.choice(moves)


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


class AlphaBetaPruning(Player):

    def __init__(self, me, you, fprune=0.1, margin=0.0):
        super(AlphaBetaPruning, self).__init__(me, you)

        # algorithm params
        self.margin = margin  # for more aggressive pruning
        self.fprune = fprune  # for unlikely random pruning

        self.overall_weight = 1.0
        self.corner_weight = 4.0
        self.g_weight = 2.0
        self.danger_weight = 2.0
        self.center_weight = 1.0
        self.move_weight = 1.1

        self.connected_weight = 1.5
        self.mobility_weight = 2.0
        self.frontiers_weight = 5.0

        self.modify_weights_at_round = 30
        self.seconds_cutoff = 9
        self.max_depth = 4

        self.t1, self.t2 = 0.0, 0.0
        self.round = -1
        self.timeLimit = time.time()

    def move(self, state):
        moves = self.get_valid_moves(state[0], state[1])
        self.time_limit = time.time() + self.seconds_cutoff

        if self.round < 4:
            return random.choice(moves)

        if self.round > self.modify_weights_at_round:
            self.overall_weight = 2.0
            self.mobility_weight = 1.0
            self.max_depth = 5

        return self.alpha_beta(moves)

    def alpha_beta(self, moves):
        def future(move):
            space = self.board.spaces[move]
            next_s = self.board.next_state_bits(space, self.mine, self.foe)
            return self.min_val(next_s, -INF, INF, depth=0)

        futures = [(future(move), move) for move in moves]
        print_futures(futures)
        best_value_move = max(futures, key=get_value)
        print("Best: ", best_value_move[1], ": ", best_value_move[0])
        return best_value_move[1]

    def stop(self, depth):
        if depth > self.max_depth:
            return True
        elif time.time() > self.time_limit:
            print("-" * depth, "Timeout")
            return True
        else:
            return False

    def min_val(self, s, alpha, beta, depth):
        if self.stop(depth):
            return self.evaluate(s, self.me)

        val = INF
        moves = self.get_valid_moves(s, self.you)

        for idx, move in enumerate(moves):
            # next_state_bits(self, space, mover, opponent):
            space = self.board.spaces[move]
            next_s = self.board.next_state_bits(space, s[1], s[0])
            val = min(val, self.max_val(next_s, alpha, beta, depth+1))
            if val - self.margin <= alpha:  # or fprune > random():
                return val
            beta = min(beta, val)

        return val

    def max_val(self, s, alpha, beta, depth):
        if self.stop(depth):
            return self.evaluate(s, self.me)

        val = -INF
        moves = self.get_valid_moves(s, self.me)

        for idx, move in enumerate(moves):
            space = self.board.spaces[move]
            next_s = self.board.next_state_bits(space, s[0], s[1])
            val = max(val, self.min_val(next_s, alpha, beta, depth+1))
            if val + self.margin >= beta:
                return val
            alpha = max(alpha, val)

        return val

    def enemy_index(self, player):
        return (player == 1) + 1

    def evaluate(self, s, player):
        enemy = self.enemy_index(player)

        # how many moves do I have vs how many moves they have
        player_moves = self.get_valid_moves(s, player)
        enemy_moves = self.get_valid_moves(s, enemy)

        mobility = len(player_moves)
        frontiers = len(enemy_moves)

        # overall = compare(score(s, player), score(s, enemy))
        my_score = self.board.score(s[0])
        foe_score = self.board.score(s[1])
        overall = (my_score - foe_score) / (my_score + foe_score)

        corners_bits = sum(self.board.spaces[i] for i in CORNERS)
        corners = (self.board.score(corners_bits & s[0]) -
                   self.board.score(corners_bits & s[1]))

        # edges_bits = sum(self.board.spaces[i] for i in G_EDGES)
        # edges = (self.board.score(edges_bits & s[0]) -
        #            self.board.score(edges_bits & s[1]))

        dangers_bits = sum(self.board.spaces[i] for i in DANGERS)
        dangers = (self.board.score(dangers_bits & s[0]) -
                   self.board.score(dangers_bits & s[1]))

        # centers_bits = sum(self.board.spaces[i] for i in CENTERS)
        # centers = (self.board.score(centers_bits & s[0]) -
        #            self.board.score(centers_bits & s[1]))

        return (self.overall_weight * overall +
                self.corner_weight * corners +
                self.danger_weight * dangers +
                self.mobility_weight * mobility -
                self.frontiers_weight * frontiers)


# -------------- #
# Stuff for MCTS #
# -------------- #

class MCTSNode(object):
    board = Board()

    def __init__(self, parent, s, c=1.4):
        self.parent = parent
        self.children = {}  # dict mapping action => MCTSNode
        # TODO: make sure starting at 0 doesn't screw things up
        self.n_visits = 0
        self.value = 0
        self.state = s
        self.c = c
        pass

    def expand(self):
        # TODO: fill me in -- add child nodes
        pass

    def select(self):
        # TODO: implement UTC or some more intelligent algo that encourages
        #       exploration
        # TODO: if all children nodes aren't in place, select a move randomly
        return max(iteritems_dict(self.children), key=lambda z: z.value)

    def _update(self, z):
        self.n_visits += 1

        # NOTE: only counting wins (positive z)!
        if z > 0:
            self.value += 1
        pass

    def backprop(self, z):
        if self.parent:
            # propogate all the way back up the tree
            self.parent.backprop(z)
        self._update(z)

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def is_root(self):
        return self.parent is None

    @property
    def value(self):
        return self.value / self.n_visits


class MCTS(object):
    def __init__(self, me, you):
        super(MCTS, self).__init__(me, you)
        # maps from (me_placed, foe_placed) => MCTSNode
        self.nodes = {(0, 0): MCTSNode(None, (0, 0))}

    def move(self, moves):
        pass



if __name__ == "__main__":

    if len(sys.argv) >= 3:
        print(('Number of arguments: ', len(sys.argv)))
        print(('Argument List: ', str(sys.argv)))
        print((str(sys.argv[1])))

        me = int(sys.argv[2])
        you = 1 if me == 2 else 2

        import cProfile
        arg = sys.argv[1]
        player = AlphaBetaPruning(me, you)
        # player = RandomPlayer(me, you)
        # player.play_game(arg)
        cProfile.run('player.play_game("{}")'.format(arg))
