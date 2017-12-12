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


class Player(object):
    def __init__(self, me, you):
        self.me, self.you = me, you
        self.round = 0

        # handling the board
        self.board = Board()
        self.centers_bits = sum(self.board.spaces[i] for i in CENTERS)
        self.corners_bits = sum(self.board.spaces[i] for i in CORNERS)
        self.mine = 0
        self.foe = 0

    def get_valid_moves(self, state, player=None):
        """
        state is: (p1_placed, p2_placed, whose_turn)
        """
        if player is None:
            player = state[2]

        if self.round < 4:
            centers_remaning_bits = self.centers_bits - state[0] - state[1]
            return self.board.bits_to_tuples(centers_remaning_bits)

        if player == 1:
            return self.board.legal_actions(state[0], state[1])
        else:
            return self.board.legal_actions(state[1], state[0])

    def play_game(self, hostname):
        def init_client(hostname):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (hostname, 3333 + self.me)
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
                self.save_tree()
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
        sock = init_client(hostname)

        #TODO load the tree here
        try:
            self.load_tree()
        except:
            print("Load tree not a method")
        while True:
            turn = read_message(sock)
            if turn == self.me:
                my_move = self.move(self.pack_state(turn))
                print("============")
                print("Round: ", self.round)
                # print("Valid moves: ", valid_moves)
                print("mine: ", self.mine)
                print("FOE: ", self.foe)
                print(self.board)
                # my_move = self.move(valid_moves)
                print("My move: ", my_move)

                msg = "{}\n{}\n".format(my_move[0], my_move[1])
                sock.send(msg.encode())

    def other_player(self, a_player):
        if a_player == self.me:
            return self.you
        else:
            return self.me

    def pack_state(self, turn):
        if self.me == 1:
            return self.mine, self.foe, turn
        else:
            return self.foe, self.mine, turn
