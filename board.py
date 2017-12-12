import sys

if sys.version_info.major == 2:
    range = xrange

# MARKERS = {0: "   ", 1: " \u25cf ", 2: " \u25cb "}
MARKERS = {0: "   ", 1: " X ", 2: " O "}
SPACES = {}
for row in range(8):
    for col in range(8):
        SPACES[(row, col)] = 1 << (8 * row + col)


class Board(object):
    def __init__(self, p1_placed=0, p2_placed=0, player_turn=1):
        self.spaces = SPACES

        self.mask_a = 0xfefefefefefefefe
        self.mask_h = 0x7f7f7f7f7f7f7f7f
        self.centers_bits = sum(
            SPACES[i] for i in [(3, 4), (4, 3), (4, 4), (3, 3)]
        )

        # the state
        self.p1_placed = p1_placed
        self.p2_placed = p2_placed
        self.player_turn = player_turn

    def init(self):
        self.p1_placed = SPACES[(3, 4)] + SPACES[(4, 3)]
        self.p2_placed = SPACES[(4, 4)] + SPACES[(3, 3)]
        self.player_turn = 1

    def __getitem__(self, index):
        return self.spaces[index]

    def __repr__(self):
        out = ""
        for row in range(8):
            for col in range(8):
                space = self.spaces[(row, col)]
                if space & self.p1_placed:
                    out += MARKERS[1]
                elif space & self.p2_placed:
                    out += MARKERS[2]
                else:
                    out += MARKERS[0]

            out += "\n"

        return out

    # def __repr__(self):
    #     buf = io.StringIO()
    #     for row in range(8):
    #         for col in range(8):
    #             space = self.spaces[(row, col)]
    #             if space & self.p1_placed:
    #                 buf.write(MARKERS[1])
    #             elif space & self.p2_placed:
    #                 buf.write(MARKERS[2])
    #             else:
    #                 buf.write(MARKERS[0])
    #
    #         buf.write("\n")
    #
    #     out = buf.getvalue()
    #     buf.close()
    #     return out

    def _one_directon_right_shift(self, g, p, n):
        g |= p & (g >> (n * 1))
        p &= (p >> (n * 1))
        g |= p & (g >> (n * 2))
        p &= (p >> (n * 2))
        g |= p & (g >> (n * 4))
        return g

    def _one_directon_left_shift(self, g, p, n):
        g |= p & (g << (n * 1))
        p &= (p << (n * 1))
        g |= p & (g << (n * 2))
        p &= (p << (n * 2))
        g |= p & (g << (n * 4))
        return g

    def _get_g_directions(self, mine, opp):
        self.mask_a = 0xfefefefefefefefe
        self.mask_h = 0x7f7f7f7f7f7f7f7f
        gN = self._one_directon_right_shift(mine, opp, 8)
        gS = self._one_directon_left_shift(mine, opp, 8)
        gE = self._one_directon_left_shift(mine, opp & self.mask_a, 1)
        gW = self._one_directon_right_shift(mine, opp & self.mask_h, 1)
        gNE = self._one_directon_right_shift(mine, opp & self.mask_a, 7)
        gNW = self._one_directon_right_shift(mine, opp & self.mask_h, 9)
        gSE = self._one_directon_left_shift(mine, opp & self.mask_a, 9)
        gSW = self._one_directon_left_shift(mine, opp & self.mask_h, 7)

        return gN, gS, gE, gW, gNE, gNW, gSE, gSW

    def legal_actions_bits(self, mine, opp):
        occupied = mine | opp
        if (self.centers_bits & occupied) != self.centers_bits:
            return self.centers_bits - occupied

        empty = 0xffffffffffffffff ^ occupied

        gN, gS, gE, gW, gNE, gNW, gSE, gSW = self._get_g_directions(mine, opp)

        legal = 0
        legal |= ((gN & ~mine) >> 8) & empty
        legal |= ((gS & ~mine) << 8) & empty
        legal |= ((gE & ~mine & self.mask_h) << 1) & empty
        legal |= ((gW & ~mine & self.mask_a) >> 1) & empty
        legal |= ((gNE & ~mine & self.mask_h) >> 7) & empty
        legal |= ((gNW & ~mine & self.mask_a) >> 9) & empty
        legal |= ((gSE & ~mine & self.mask_h) << 9) & empty
        legal |= ((gSW & ~mine & self.mask_a) << 7) & empty

        return legal

    def next_state_bits(self, action, mover, opponent):
        flips = 0
        gN, gS, gE, gW, gNE, gNW, gSE, gSW = self._get_g_directions(
            action, opponent
        )
        mover += action

        if (gN >> 8) & mover > 0:
            flips |= gN
        if (gS << 8) & mover > 0:
            flips |= gS
        if (gE << 1) & self.mask_a & mover > 0:
            flips |= gE
        if (gW >> 1) & self.mask_h & mover > 0:
            flips |= gW
        if (gNE >> 7) & self.mask_a & mover > 0:
            flips |= gNE
        if (gNW >> 9) & self.mask_h & mover > 0:
            flips |= gNW
        if (gSE << 9) & self.mask_a & mover > 0:
            flips |= gSE
        if (gSW << 7) & self.mask_h & mover > 0:
            flips |= gSW

        new_mover = mover | flips
        new_opponent = opponent & ~flips

        return new_mover, new_opponent

    # def _move_one_direction(self, mine, mask, n):
    #     flipL = mask & (mine << n)
    #     flipL |= mask & (flipL << n)
    #     maskL = mask & (mask << n)
    #     flipL |= maskL & (flipL << (2 * n))
    #     flipL |= maskL & (flipL << (2 * n))
    #     flipR = mask & (mine >> n)
    #     flipR |= mask & (flipR >> n)
    #     maskR = mask & (mask >> n)
    #     flipR |= maskR & (flipR >> (2 * n))
    #     flipR |= maskR & (flipR >> (2 * n))
    #     return (flipL << n) | (flipR >> n)
    #
    # def legal_actions_bits(self, mine, opp):
    #     # https://github.com/lk16/dots/blob/master/board/board.go
    #     mask = opp & 0x7E7E7E7E7E7E7E7E
    #     moves = self._move_one_direction(mine, mask, 1)
    #     moves |= self._move_one_direction(mine, mask, 7)
    #     moves |= self._move_one_direction(mine, mask, 9)
    #     moves |= self._move_one_direction(mine, opp, 8)
    #     moves = moves & (~(mine | opp))
    #     return moves

    def score(self, positions):
        return bin(positions).count("1")

    def bits_to_tuples(self, bits):
        out = []
        for row in range(8):
            for col in range(8):
                space = self.spaces[(row, col)]
                if space & bits > 0:
                    out.append((row, col))

        return out

    def legal_actions(self, mine, opp):
        moves = self.legal_actions_bits(mine, opp)
        return self.bits_to_tuples(moves)

    def is_over(self, mine=None, opp=None):
        if mine is None:
            if opp is not None:
                raise ValueError("Must pass both or neither of mine and opp")

            mine = self.p1_placed
            opp = self.p2_placed

        if mine == 0 or opp == 0:
            # someone got wiped out
            return True

        occupied = mine | opp
        if occupied == (1 << 64) - 1:
            # board full
            return True

        if (len(self.legal_actions(mine, opp)) == 0 and
            len(self.legal_actions(opp, mine)) == 0):
            # no one can move
            return True

        # keep going!
        return False

    def get_moves(self):
        if self.player_turn == 1:
            return self.legal_actions(self.p1_placed, self.p2_placed)
        else:
            return self.legal_actions(self.p2_placed, self.p1_placed)

    def do_action(self, action):
        if self.player_turn == 1:
            self.p1_placed, self.p2_placed = self.next_state_bits(
                action, self.p1_placed, self.p2_placed
            )
            self.player_turn = 2
        else:
            self.p2_placed, self.p1_placed = self.next_state_bits(
                action, self.p2_placed, self.p1_placed
            )
            self.player_turn = 1

        return self.p1_placed, self.p2_placed, self.player_turn

    def player_passes(self):
        self.player_turn = (self.player_turn == 1) + 1
        return self.p1_placed, self.p2_placed, self.player_turn

    def set_state(self, state):
        self.p1_placed, self.p2_placed, self.player_turn = state
