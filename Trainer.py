import os
import subprocess
import sys
import time

if sys.version_info.major == 2:
    input = raw_input


ROOT_DIR = os.getcwd()

commands_for_ai = {
    "qualifier": ["java" ,"-jar", "MCTS.jar" , "localhost"],
    "random": ["python", "main.py", "localhost", "random"],
    "MCTS": ["python", "main.py", "localhost", "MCTS"],
    "alpha-beta": ["python", "main.py", "localhost", "alphabeta"]
}

def run_game(player1AI, player2AI):
    print("Startin game with player1 =", player1AI, "and player2 =", player2AI)
    process = start_server()
    start_player1(player1AI)
    start_player2(player2AI)
    process.wait()

    # wait for game to end
def start_server():
    os.chdir(ROOT_DIR+"/ReversiServer")
    args = ["java", "Reversi", "3"]
    # completed = subprocess.run(args, stdout=subprocess.PIPE)

    process = subprocess.Popen(args)
    time.sleep(2)
    return process

def start_player1(ai_type):
    print("\nStarting player 1: ", ai_type)
    # Need to fork here?
    os.chdir(ROOT_DIR)
    command = list(commands_for_ai[ai_type])
    command.append("1")
    print("Command: ", command)

    if ai_type == "qualifier":
        # Qualifier. Need to pass in 1 after process starts
        p1_process = subprocess.Popen(command, stdin=subprocess.PIPE, encoding="utf8")
        time.sleep(1)
        try:
            p1_process.communicate(input="1\n", timeout=1)
        except:
            print("done waiting")
    else:
        subprocess.Popen(command)
        time.sleep(2)

def start_player2(ai_type):
    print("\nStarting player 2")
    os.chdir(ROOT_DIR)
    command = list(commands_for_ai[ai_type])
    command.append("2")
    if ai_type == "qualifier":
        # Qualifier. Need to pass in 1 after process starts
        p2_process = subprocess.Popen(command, stdin=subprocess.PIPE, encoding="utf8")
        time.sleep(1)
        try:
            p2_process.communicate(input="1\n", timeout=1)
        except:
            print("done waiting")
    else:
        subprocess.Popen(command)
        time.sleep(2)

if __name__ == "__main__":
    # Get number of rounds from input
    ais = ["qualifier", "random", "MCTS", "alpha-beta"]
    msg = """\n\n\nSelect AI for player {}:
    0: qualifier
    1: random
    2: MCTS
    3: alpha-beta pruning

    """

    player1AI = int(input(msg.format(1)))
    print("Selected ", ais[player1AI], "for player 1")

    player2AI = int(input(msg.format(2)))
    print("Selected ", ais[player2AI], "for player 2")

    rounds = int(input("How many games to perform? "))
    print("Starting trainer with", rounds, "rounds")

    for round in range(rounds):
        # alternate who goes first
        print("Game ", round, "/", rounds)
        if round % 2:
            run_game(ais[player2AI], ais[player1AI])
        else:
            run_game(ais[player1AI], ais[player2AI])

    print("Done running all games!")
