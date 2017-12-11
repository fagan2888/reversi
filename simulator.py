from board import Board


class Simulator(object):
    def __init__(self, p1, p2, state=None):
        self.p1 = p1
        self.p2 = p2
        if state is None:
            self.board = Board()
            self.board.init()
        else:
            self.board = Board(state[0], state[1])
            self.board.player_turn = state[2]

    # 100 moves is more than the max (64), so a whole game will be played
    def run_simulation(self,  disp=False):
        while True:
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
