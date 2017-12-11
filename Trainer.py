import os
import subprocess

ROOT_DIR = os.getcwd()

ai_types = {
    "qualifier": ["java" ,"-jar", "MCTS" , "localhost"],
    "random": ["python", "main.py", "localhost", "random"],
    "MCTS": ["python", "main.py", "localhost", "MCTS"],
    "alpha-beta": ["python", "main.py", "localhost", "alphabeta"]
}

def run_game(player1AI, player2AI):
    print("Startin game with player1 =", player1AI, "and player2 =", player2AI)
    start_server()
    print("run game, after start_server")
    start_player1(player1AI)
    print("run game, after start_player1")
    start_player2(player2AI)
    print("run game, after start_player2")

    # wait for game to end
def start_server():
    os.chdir(ROOT_DIR+"/ReversiServer")
    args = ["java", "Reversi", "3"]
    completed = subprocess.run(args, stdout=subprocess.PIPE)
    print("start_server, after subprocess.run")

def start_player1(ai_type):
    # Need to fork here?
    os.chdir(ROOT_DIR)
    command = ai_types[ai_type].append("1")

    if ai_type == 0:
        # Qualifier. Need to pass in 1 after process starts
        print("qualifier")
    else:
        completed = subprocess.run(command)

def start_player2(ai_type):
    os.chdir(ROOT_DIR)
    command = ai_types[ai_type].append("2")
    if ai_type == 0:
        # Qualifier. Need to pass in 1 after process starts
        print("qualifier")
    else:
        completed = subprocess.run(command)

if __name__ == "__main__":
    # Get number of rounds from input
    ais = ["qualifier", "random", "MCTS", "alpha-beta"]

    player1AI = int(input("Select player 1 AI: \n\t0: qualifier\n\t1: random\n\t2: MCTS\n\t3: alpha-beta\n"))
    print("Selected ", ais[player1AI], "for player 1")

    player2AI = int(input("Select player 2 AI: \n\t0: qualifier\n\t1: random\n\t2: MCTS\n\t3: alpha-beta\n"))
    print("Selected ", ais[player2AI], "for player 2")

    rounds = int(input("How many games to perform? "))
    print("Starting trainer with", rounds, "rounds")

    run_game(ais[player1AI], ais[player2AI])
    # for round in range(rounds):
    #     # alternate who goes first
    #     print("Game ", round, "/", rounds)
    #     if round % 2:
    #         run_game(ais[player1AI], ais[player2AI])
    #     else:
    #         run_game(ais[player2AI], ais[player1AI])
