module Reversi

using Parameters

struct State
    p1_placed::UInt64
    p2_placed::UInt64
    player::Int
    round::Int
end
State() = State(0, 0, 1, 0)

encode(r::Integer, c::Integer) = UInt64(1) << (8*(r-1) + (c-1))
encode(rc::Tuple{Integer,Integer}) = encode(rc[1], rc[2])
const MARKERS = Dict(0 => "   ", 2 => " \u25cf ", 1 => " \u25cb ")
const CENTERS_BITS = sum(encode(i) for i in [(4, 4), (5, 5), (5, 4), (4, 5)])

function show_board(io::IO, s::State)
    @unpack p1_placed, p2_placed = s
    # corners
    top_left = "\u250C"
    top_right = "\u2510"
    bottom_left = "\u2514"
    bottom_right = "\u2518"

    # lines
    hori = "\u2500"
    vert = "\u2502"

    # line + center piece
    hori_down = "\u252C"
    hori_up = "\u2534"

    print(io, " ", join(map(i->string("  ", i, " "), 1:8)), "\n")
    print(io, " ", top_left, hori, repeat(string(hori^2, hori_down, hori), 7), hori^2, top_right)

    for r in UInt64(1):8
        println(io)
        print(io, r)
        print(io, vert)
        for c in UInt64(1):8
            v = encode(r, c)
            if v & p1_placed > 0
                print(io, MARKERS[1])
            elseif v & p2_placed > 0
                print(io, MARKERS[2])
            else
                print(io, MARKERS[0])
            end
            print(io, vert)
        end
    end

    println(io, "\n ", bottom_left, hori, repeat(string(hori^2, hori_up, hori), 7), hori^2, bottom_right)
end

function Base.show(io::IO, s::State)
    @unpack player, round = s
    if player == 1 || player == 2
        msg = "It is Player $(player)'s ($(MARKERS[player])) turn"
    else
        msg = "It is player $(player)'s turn"
    end

    println(io, msg, " on round $round")
    println(io, "The score is $(score(s)) and the board looks like:\n")
    show_board(io, s)
end

# -------------- #
# bitboard stuff #
# -------------- #

function _one_directon_right_shift(g::UInt64, p::UInt64, n::Integer)
    g |= p & (g >> (n * 1))
    p &= (p >> (n * 1))
    g |= p & (g >> (n * 2))
    p &= (p >> (n * 2))
    g |= p & (g >> (n * 4))
    g
end

function _one_directon_left_shift(g::UInt64, p::UInt64, n::Integer)
    g |= p & (g << (n * 1))
    p &= (p << (n * 1))
    g |= p & (g << (n * 2))
    p &= (p << (n * 2))
    g |= p & (g << (n * 4))
    g
end

function _get_g_directions(p1::UInt64, p2::UInt64)
    mask_a = 0xfefefefefefefefe
    mask_h = 0x7f7f7f7f7f7f7f7f

    gN = _one_directon_right_shift(p1, p2, 8)
    gS = _one_directon_left_shift(p1, p2, 8)
    gE = _one_directon_left_shift(p1, p2 & mask_a, 1)
    gW = _one_directon_right_shift(p1, p2 & mask_h, 1)
    gNE = _one_directon_right_shift(p1, p2 & mask_a, 7)
    gNW = _one_directon_right_shift(p1, p2 & mask_h, 9)
    gSE = _one_directon_left_shift(p1, p2 & mask_a, 9)
    gSW = _one_directon_left_shift(p1, p2 & mask_h, 7)

    return gN, gS, gE, gW, gNE, gNW, gSE, gSW
end

function legal_actions_bits(mover::UInt64, opp::UInt64)
    occupied = mover | opp
    if (CENTERS_BITS & occupied) != CENTERS_BITS
        return CENTERS_BITS - occupied
    end

    mask_a = 0xfefefefefefefefe
    mask_h = 0x7f7f7f7f7f7f7f7f
    empty = 0xffffffffffffffff ⊻ occupied

    gN, gS, gE, gW, gNE, gNW, gSE, gSW = _get_g_directions(mover, opp)

    legal = UInt64(0)
    legal |= ((gN & ~mover) >> 8) & empty
    legal |= ((gS & ~mover) << 8) & empty
    legal |= ((gE & ~mover & mask_h) << 1) & empty
    legal |= ((gW & ~mover & mask_a) >> 1) & empty
    legal |= ((gNE & ~mover & mask_h) >> 7) & empty
    legal |= ((gNW & ~mover & mask_a) >> 9) & empty
    legal |= ((gSE & ~mover & mask_h) << 9) & empty
    legal |= ((gSW & ~mover & mask_a) << 7) & empty
    legal
end

function next_state_bits(action::UInt64, mover::UInt64, opponent::UInt64)
    flips = UInt64(0)
    gN, gS, gE, gW, gNE, gNW, gSE, gSW = _get_g_directions(
        action, opponent
    )

    mask_a = 0xfefefefefefefefe
    mask_h = 0x7f7f7f7f7f7f7f7f
    mover += action

    ((gN >> 8) & mover > 0)           && (flips |= gN)
    ((gS << 8) & mover > 0)           && (flips |= gS)
    ((gE << 1) & mask_a & mover > 0)  && (flips |= gE)
    ((gW >> 1) & mask_h & mover > 0)  && (flips |= gW)
    ((gNE >> 7) & mask_a & mover > 0) && (flips |= gNE)
    ((gNW >> 9) & mask_h & mover > 0) && (flips |= gNW)
    ((gSE << 9) & mask_a & mover > 0) && (flips |= gSE)
    ((gSW << 7) & mask_h & mover > 0) && (flips |= gSW)

    new_mover = mover | flips
    new_opponent = opponent & (~flips)

    new_mover, new_opponent
end

score(x::UInt64) = count_ones(x)
function bits_to_tuples(x::UInt64)
    out = Tuple{Int,Int}[]
    for r in 1:8
        for c in 1:8
            v = encode(r, c)
            if v & x > 0
                push!(out, (r, c))
            end
        end
    end
    out
end

legal_actions(p1::UInt64, p2::UInt64) = bits_to_tuples(legal_actions_bits(p1, p2))

function game_over(p1::UInt64, p2::UInt64)::Tuple{Bool,Int,Int}
    if p1 == 0
        return true, 0, score(p2)
    end

    if p2 == 0
        return true, score(p1), 0
    end

    occupied = p1 | p2
    if occupied == (UInt64(1) << (64)) - 1
        return true, score(p1), score(p2)
    end

    if isempty(legal_actions(p1, p2)) && isempty(legal_actions(p2, p1))
        return true, score(p1), score(p2)
    end

    false, 0, 0
end

do_pass(s::State) = State(s.p1_placed, s.p2_placed, (s.player == 1) + 1, s.round+1)

# --------------------------- #
# bitboard api for State type #
# --------------------------- #

function legal_actions_bits(s::State)
    @unpack p1_placed, p2_placed, player = s
    if player == 1
        return legal_actions_bits(p1_placed, p2_placed)
    else
        return legal_actions_bits(p2_placed, p1_placed)
    end
end

score(s::State) = score(s.p1_placed), score(s.p2_placed)
legal_actions(s::State) = bits_to_tuples(legal_actions_bits(s))
function game_over(s::State)
    if s.round  < 4
        return false, 0, 0
    end
    game_over(s.p1_placed, s.p2_placed)
end

function do_action(s::State, action::UInt64)::State
    @unpack p1_placed, p2_placed, player = s
    if player == 1
        new_p1, new_p2 = next_state_bits(action, p1_placed, p2_placed)
        new_player = 2
    else
        new_p2, new_p1 = next_state_bits(action, p2_placed, p1_placed)
        new_player = 1
    end
    State(new_p1, new_p2, new_player, s.round+1)
end

do_action(s::State, a::Tuple{Int,Int}) = do_action(s, encode(a))

opponent(i::Integer) = (i == 1) + 1
opponent(s::State) = opponent(state.player)

# ---------- #
# Simulation #
# ---------- #
abstract type Player end

"Using players `p1` and `p2`, simulate the game starting from state `s`"
function play_game(p1::Player, p2::Player, s::State=State(); disp::Bool=true)
    players = (p1, p2)
    while !(game_over(s)[1])
        disp && show(s)
        actions_bits = legal_actions_bits(s)
        if actions_bits == 0
            s = do_pass(s)
            continue
        end
        action = select_action(players[s.player], s)
        s = do_action(s, action)
    end
    score(s)
end

# ------- #
# Players #
# ------- #

select_action(p::Player, s::State) = select_action(p, s, legal_actions(s))
select_action(p::Player, s::State, g::Base.Generator) = select_action(p, s, collect(g))
select_action(p::Player, s::State, a::UInt64) = select_action(p, s, bits_to_tuples(a))

struct RandomPlayer <: Player end
function select_action(
        p::RandomPlayer, s::State, actions::AbstractVector{Tuple{Int,Int}}
    )
    rand(actions)
end

# ---------- #
# Evaluators #
# ---------- #

function weighted_evaluator(s::State)
    # TODO: optimize over these weights
    weights = Float64[
        120 -20  20   5   5  20 -20 120
        -20 -40  -5  -5  -5  -5 -40 -20
         20  -5  15   3   3  15  -5  20
          5  -5   3   3   3   3  -5   5
          5  -5   3   3   3   3  -5   5
         20  -5  15   3   3  15  -5  20
        -20 -40  -5  -5  -5  -5 -40 -20
        120 -20  20   5   5  20 -20 120
    ]
    p1_score = 0.0
    for (r, c) in bits_to_tuples(s.p1_placed)
        p1_score += weights[r, c]
    end

    p2_score = 0.0
    for (r, c) in bits_to_tuples(s.p1_placed)
        p1_score += weights[r, c]
    end

    p1_score, p2_score
end

# ------- #
# Minimax #
# ------- #

struct Minimax{Teval} <: Player
    evaluator::Teval
    depth::Int
end

function minimax(p::Minimax, s::State, depth::Int)
    if depth == 0 || game_over(s)[1]
        vals = p.evaluator(s)
        val = vals[1] - vals[2]
        if s.player == 1
            return val, (0, 0)
        else
            return -val, (0, 0)
        end
    end

    value(a_state::State) = -minimax(p, a_state, depth-1)[1]

    actions = legal_actions(s)

    if length(actions) == 0  # this guy can't go. Let him pass
        return value(do_pass(s)), (0, 0)
    end

    return maximum((value(do_action(s, a)), a) for a in actions)
end

select_action(p::Minimax, s::State) = minimax(p, s, p.depth)[2]

# ------------------ #
# Alpha beta pruning #
# ------------------ #

struct AlphaBetaPruning{Teval} <: Player
    evaluator::Teval
    depth::Int
end

function alphabeta(p::AlphaBetaPruning, s::State, depth::Int, alpha, beta)
    if depth == 0 || game_over(s)[1]
        vals = p.evaluator(s)
        val = vals[1] - vals[2]
        if s.player == 1
            return val, (0, 0)
        else
            return -val, (0, 0)
        end
    end

    actions = legal_actions(s)

    if length(actions) == 0  # this guy can't go. Let him pass
        return -alphabeta(p, do_pass(s), depth-1, -beta, -alpha)[1], (0, 0)
    end

    best_action = actions[1]
    for action in actions
        if alpha >= beta
            break
        end
        val = -alphabeta(p, do_action(s, action), depth-1, -beta, -alpha)[1]
        if val > alpha
            alpha = val
            best_action = action
        end
    end
    return alpha, best_action
end

select_action(p::AlphaBetaPruning, s::State) = alphabeta(p, s, p.depth, -Inf, Inf)[2]

# ----------------- #
# Tournament Server #
# ----------------- #

function read_message(sock::TCPSocket)
    turn = parse(Int, readline(sock))
    round = parse(Int, readline(sock))
    t1 = parse(Float64, readline(sock))
    t2 = parse(Float64, readline(sock))
    p1_placed = UInt64(0)
    p2_placed = UInt64(0)
    for i in 1:8, j in 1:8
        owned = parse(Int, readline(sock))
        if owned == 1
            p1_placed += encode(9-i, j)
        elseif owned == 2
            p2_placed += encode(9-i, j)
        end
    end
    readline(sock)
    State(p1_placed, p2_placed, turn, round)
end

play_move(sock::TCPSocket, rc::Tuple{Int, Int}) = play_move(sock, rc[1], rc[2])
play_move(sock::TCPSocket, row, col) = write(sock, string(8-row, '\n', col-1, '\n'))

struct TournamentPlayer{Tp<:Player}
    player::Tp
    me::Int
    them::Int
end

TournamentPlayer(p::Player, me::Int) = TournamentPlayer(p, me, (me == 1) + 1)

function update_msg(tp::TournamentPlayer, s::State)
    @unpack me, them = tp
    the_score = score(s)
    if the_score[me] > the_score[them]
        println("Winning $(the_score[me]) to $(the_score[them])")
    else
        println("Losing $(the_score[me]) to $(the_score[them])")
    end
    println("Here's what the board looks like:")
    show_board(STDOUT, s)
end

function play_game(tp::TournamentPlayer)
    @unpack me, them = tp
    sock = connect(3333 + me)
    @show readline(sock)

    while true
        s = read_message(sock)
        if s.player == -999
            final_score = score(s)
            if final_score[me] > final_score[them]
                msg = "Congrats, you won "
            else
                msg = "Sorry, you lost "
            end
            println(msg, "by a score of ", final_score)
            break
        end
        if s.player == me
            update_msg(tp, s)
            play_move(sock, select_action(tp.player, s))
        end
    end
end

#=
usage:

include("reversi.jl")
player = Reversi.AlphaBetaPruning(Reversi.weighted_evaluator, 9)

# assume we are player 2
tp = Reversi.TournamentPlayer(player, 2)
Reversi.play_game(tp)
=#

#=
TODO:

- Make depth depend on time remaining
- Make weights depend on tile positions
- Do rollouts in parallel
- Memoize?
- Do training to optimize weights
=#

end # module
