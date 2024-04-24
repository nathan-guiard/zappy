import socket
import argparse
import json
import random
from color import color
import copy
import multiprocessing
import signal
import sys


# Variable Globale
Debug : bool
Client : socket
Direction = ['N', 'E', 'S', 'W']
Player: dict
list_processus: multiprocessing.Process

levels = {
        1: {"Linemate": 1},
        2: {"Linemate": 1, "Deraumere": 1, "Sibur": 1},
        3: {"Linemate": 2, "Sibur": 1, "Phiras": 2},
        4: {"Linemate": 1, "Deraumere": 1, "Sibur": 2, "Phiras": 1},
        5: {"Linemate": 1, "Deraumere": 2, "Sibur": 1, "Mendiane": 3},
        6: {"Linemate": 1, "Deraumere": 2, "Sibur": 3, "Phiras": 1},
        7: {"Linemate": 2, "Deraumere": 2, "Sibur": 2, "Mendiane": 2, "Phiras": 2, "Thystame": 1},
}

def parser():
    parser = argparse.ArgumentParser(description='Client program', add_help=False)
    parser.add_argument('-n', '--team', type=str, help='Team name', required=True)
    parser.add_argument('-p', '--port', type=int, help='Port number', required=True)
    parser.add_argument('-h', '--hostname', type=str, help='Hostname', default='localhost')
    parser.add_argument('-d', '--debug', action='store_true', help=argparse.SUPPRESS)

    args = parser.parse_args()

    global Debug
    Debug = args.debug

    # Vérification des valeurs des arguments
    if not 1024 <= args.port <= 65535:
        sys.stderr.write("Erreur: Le numéro de port doit être compris entre 1024 et 65535.\n")
        sys.exit(1)
    if Debug:
        print("Nom de l'équipe:", args.team)
        print("Numéro de port:", args.port)
        print("Nom d'hôte:", args.hostname)
        print("Debug:", args.debug)
    return args

def server_connexion(host, port, team):
    global Client
    if Debug: 
        print("Connexion...")
    try:
        Client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Client.settimeout(30)
        Client.connect((host, port))
    except socket.timeout:
        sys.stderr.write("Timeout: Connexion au serveur expirée\n")
        sys.exit(1)
    except ConnectionRefusedError:
        sys.stderr.write("Erreur de connexion: Connexion refusée\n")
        sys.exit(1)
    if Debug:
        print(f"Connexion vers {host}:{port} reussie.")
    Client.send("".encode())
    response = Client.recv(1024).decode()
    print(response)
    Client.send((team + '\n').encode())
    response: str = Client.recv(1024).decode()
    if response.endswith == "does not exist\n":
        sys.stderr.write(response)
        Client.close()
        sys.exit(1)
    elif response.startswith("0\n"):
        sys.stderr.write(f"The team {team} is full\n")
        Client.close()
        sys.exit(1)
    return response

def init(hostname, port, team, id): 
    connexion_and_map_size = server_connexion(hostname, port, team)
    global list_processus, Player_id
    list_processus = []
    Player_id = id
    global Player
    Player = {}
    Player["direction"] = 'N'
    connexion_and_map_size = connexion_and_map_size.split('\n')
    Player["connexion"] = connexion_and_map_size[0]
    Player["map_size"] = tuple(map(int, connexion_and_map_size[1].split()))
    Player["map"] = [[{} for x in range(Player["map_size"][0])] for y in range(Player["map_size"][1])]
    Player["level"] = 1
    Player["fork_nb"] = 3 - Player_id if Player_id < 3 else 0

def get_player_position(vision_data):
    if vision_data and isinstance(vision_data[0], dict) and "p" in vision_data[0]:
        # Mettre à jour la position du joueur
        Player["position"] = (vision_data[0]["p"]["x"], vision_data[0]["p"]["y"])

def update_tile_content(content):
    if "Player" in content:
        content["Player"] -= 1
        if content["Player"] == 0:
            del content["Player"]

def update_map_with_vision():
    v = None
    try :
        vision_data = send_command("voir")
        v = vision_data
        vision_data = json.loads(vision_data)
        get_player_position(vision_data)
        for tile in vision_data:
            position = (tile["p"]["x"], tile["p"]["y"])
            content = {k: v for d in tile["c"] for k, v in d.items()}
            content = {**content, **tile["p"]}
            update_tile_content(content)
            Player["map"][position[1]][position[0]] = content
    except json.JSONDecodeError as e:
        sys.stderr.write(color(f"Erreur JSON lors de la mise à jour de la carte avec la vision : {e}\nwith : '{v}'\n", "red_bg"))
        send_command("voir")


def send_command(command) -> str:
    Client.send((command + '\n').encode())
    try :
        response:str = Client.recv(1024).decode()
    except socket.timeout or ConnectionResetError:
        sys.stderr.write("Tu es mort timeout\n")
        wait_and_exit()
    if response == "You died\n":
        sys.stderr.write("Tu es mort reponse de mort\n")
        wait_and_exit()
    elif response.startswith("End of game"):
        print(end=response)
        wait_and_exit()
    elif response.startswith("Disconnected"):
        print(end=response)
        wait_and_exit()
    if True:
        print(f"ID:{Player_id} || {color(command, 'red')} : {color(' '.join(response.split()), 'lightgreen')}")
    
    return response

def calculate_moves(x_dest, y_dest):
    def wrapped_distance(a, b, size):
        choix = ((a - b) % size, (b - a) % size)
        return "moins" if choix.index(min(choix)) == 0 else "plus", min(choix)
    moves = []
    x, y, direction = Player["position"][0], Player["position"][1], Player["direction"]
    if Debug:
        print(color("calculate_moves:", "purple"), x, y, x_dest, y_dest, direction)
    
    direction_x, distance_x = wrapped_distance(x, x_dest, Player["map_size"][0])
    direction_y, distance_y = wrapped_distance(y, y_dest, Player["map_size"][1])
    
    # Bouger verticalement
    while distance_y:
        if direction_y == "moins":  #monter
            if direction == 'E':
                moves.append("gauche")
                direction = 'N'
            elif direction == 'S':
                moves.append("gauche")
                moves.append("gauche")
                direction = 'N'
            elif direction == 'W':
                moves.append("droite")
                direction = 'N'
            if direction == 'N':
                moves.append("avance")
                distance_y -= 1
        elif direction_y == "plus": #descendre
            if direction == 'W':
                moves.append("gauche")
                direction = 'S'
            elif direction == 'N':
                moves.append("gauche")
                moves.append("gauche")
                direction = 'S'
            elif direction == 'E':
                moves.append("droite")
                direction = 'S'
            if direction == 'S':
                moves.append("avance")
                distance_y -= 1

    # Bouger verticalement
    while distance_x:
        if direction_x == "moins":  #gauche
            if direction == 'N':
                moves.append("gauche")
                direction = 'W'
            elif direction == 'E':
                moves.append("gauche")
                moves.append("gauche")
                direction = 'W'
            elif direction == 'S':
                moves.append("droite")
                direction = 'W'
            if direction == 'W':
                moves.append("avance")
                distance_x -= 1
        elif direction_x == "plus": #droite
            if direction == 'S':
                moves.append("gauche")
                direction = 'E'
            elif direction == 'W':
                moves.append("gauche")
                moves.append("gauche")
                direction = 'E'
            elif direction == 'N':
                moves.append("droite")
                direction = 'E'
            if direction == 'E':
                moves.append("avance")
                distance_x -= 1
    Player["direction"] = direction
    return moves

def prendre(consommables, x, y):
    while consommables:
        items = [i for i in consommables]
        focus_items = random.choices(items, k=1)[0]
        response = send_command(f"prend {focus_items}")
        if response[:2] == "ko":
            if Debug:
                print(color(f"Prendre {focus_items} fail -> update la vision", "red_bg"))
            update_map_with_vision()
            return
        consommables[focus_items] -= 1
        Player["map"][y][x][focus_items] -= 1
        if not consommables[focus_items]:
            del consommables[focus_items]
            del Player["map"][y][x][focus_items]
        if Debug:
            print(color("Reste sur case:", "purple"), consommables)
            print(Player["map"][y][x])

def map_print(passage, x, y, taillex, tailley):
    m = [[" " for _ in range(taillex)] for i in range(tailley)]
    print("size map", len(m), len(m[0]))
    print("passage", passage)
    for coord in passage:
        m[coord['y']][coord['x']] = color(f"{len(coord) - 2}", "blue")
    m[y][x] = color(f'{m[y][x]}', "red_bg")
    print(" " + "-" * (taillex))
    for i in m :
        print("|", *i, "|", sep="")
    print(" " + "-" * (taillex))
    
def score_by_level(consommable: dict): 
    # Définir les coefficients des ressources en fonction du niveau du joueur
    # Coef
    # "Linemate": 2, "Deraumere": 3, "Sibur": 4, "Mendiane": 5, "Phiras": 6, "Thystame": 10

    resource_coefficients = {
        1: {'Linemate': 2, 'Deraumere': 0, 'Sibur': 0, 'Mendiane': 0, 'Phiras': 0, 'Thystame': 0, 'Food': 1},
        2: {'Linemate': 2, 'Deraumere': 3, 'Sibur': 4, 'Mendiane': 0, 'Phiras': 0, 'Thystame': 0, 'Food': 1},
        3: {'Linemate': 4, 'Sibur': 4, 'Phiras': 12, 'Deraumere': 0, 'Mendiane': 0, 'Thystame': 0, 'Food': 1},
        4: {'Linemate': 2, 'Deraumere': 3, 'Sibur': 8, 'Phiras': 6, 'Mendiane': 0, 'Thystame': 0, 'Food': 1},
        5: {'Linemate': 2, 'Deraumere': 6, 'Sibur': 4, 'Mendiane': 15, 'Phiras': 0, 'Thystame': 0, 'Food': 1},
        6: {'Linemate': 2, 'Deraumere': 6, 'Sibur': 12, 'Phiras': 6, 'Mendiane': 0, 'Thystame': 0, 'Food': 1},
        7: {'Linemate': 4, 'Deraumere': 6, 'Sibur': 8, 'Mendiane': 10, 'Phiras': 12, 'Thystame': 10, 'Food': 1}
    }
    
    # Calculer le score en tenant compte des coefficients
    score = sum(quantity * resource_coefficients[Player["level"]].get(resource, 1)
                for resource, quantity in consommable.items())
    return score

def calculate_best_move():
    # Liste des positions adjacentes
    adjacent_positions = [row for col in Player["map"] for row in col if row]
    max_score = float('-inf')
    best_moves = []
    
    if Debug:
        map_print(adjacent_positions, Player["position"][0], Player["position"][1], Player["map_size"][0], Player["map_size"][1])
    
    for case in adjacent_positions:
        if [case["x"], case["y"]] == [Player["position"][0], Player["position"][1]]:
            actual_ressource = {key: item for key, item in case.items() if key not in ['x', 'y', 'Player']}
        consommable_tested = {key: item for key, item in case.items() if key not in ['x', 'y', 'Player']}
        
        
        score = score_by_level(consommable_tested)
        
        if score > max_score and score > 0 and consommable_tested:
            best_moves = [case["x"], case["y"]]
            max_score = score
            consommable = copy.deepcopy(consommable_tested)
    # Calculer les mouvements pour atteindre la meilleure position
    if best_moves:
        if Debug:
            print(f"{color('Actual:', 'purple')}", actual_ressource)
            print(f"{color('Search:', 'purple')}", consommable)
        if actual_ressource:
            if Debug:
                print(f"{color('Prise des ressources case actuelle', 'red_bg')}", actual_ressource)
            prendre(actual_ressource, Player["position"][0], Player["position"][1])
        
        elif best_moves == [Player["position"][0], Player["position"][1]]:
            if Debug:
                print(f"{color('Same place', 'red_bg')}", consommable)
            prendre(consommable, *best_moves)
        return calculate_moves(best_moves[0], best_moves[1])
    else:
        # Avancer de x en fonction de la vision du joueur pour eviter de voir pour rien
        if Debug:
            print(f"{color('Avance random', 'red_bg')}", Player["direction"])
        # Si aucune position adjacente n'a de ressources, rester sur place
        direction = random.choices(['avance', 'droite', 'gauche'], weights=[0.8, 0.1, 0.1], k=1)[0]
        if direction == "droite":
            Player["direction"] = Direction[(Direction.index(Player["direction"]) + 1) % 4]
        elif direction == "gauche":
            Player["direction"] = Direction[Direction.index(Player["direction"]) - 1]
        if Debug:
            print(f"random : {direction}\nnouvelle direction : {Player['direction']}")
        update_map_with_vision()
        return [direction]

def update_inventory():
    response = send_command("inventaire")
    inventory_data = json.loads(response)
    # print(f"{color('Inventaire', 'red')} : {color(' '.join(response.split()), 'lightgreen')}")
    inventory = {}
    for item in inventory_data:
        for key, value in item.items():
            inventory[key] = value
    Player["inventory"] = inventory

def check_level_requirements():
    level, inventory = Player["level"], Player["inventory"]
    
    requirements = levels[level]
    for item, quantity in requirements.items():
        if item not in inventory or inventory[item] < quantity:
            return False
    return True

def level_up():
    requirements = levels[Player["level"]]
    for item, quantity in requirements.items():
        for _ in range(quantity):
            send_command(f"pose {item}")
        Player["inventory"][item] -= quantity
        if not Player["inventory"][item]:
            del Player["inventory"][item]
    response = send_command("incantation")
    if response.startswith("ko"):
        send_command("voir")
        send_command("inventaire")
        return
    Player["level"] += 1
    Player["fork_nb"] = 0
    print(color(f"Succesfully level up {Player['level']}", "blue"))
    
def check_capacity():
    return int(send_command("connect")) > 0

def fork():
    nouveau_processus = multiprocessing.Process(target=main, args=(Player_id + 1,))
    nouveau_processus.start()
    nouveau_processus.join(timeout=0.2)
    if not nouveau_processus.is_alive():
        Player["fork_nb"] += 1
        print(color("Process est pas cree", "red_bg"))
    else :
        list_processus.append(nouveau_processus)


def wait_and_exit():
    for nouveau_processus in list_processus:
        nouveau_processus.join()
    Client.close()
    sys.exit(0)

def sigint_handler(signal, frame):
    if Player_id == 0:
        print("SIGINT reçu, fermeture du client")
    for nouveau_processus in list_processus:
        nouveau_processus.terminate()
    Client.close()
    sys.exit(0)


def main(id: int = 0, args=None):
    args = parser()
    # Initialisation du joueur
    # print(args)
    init(args.hostname, args.port, args.team, id)
    signal.signal(signal.SIGINT, sigint_handler)
            
    while True :
    
        # Demander la vision au serveur
        update_inventory()
        if check_level_requirements():
            if Debug:
                print(color("Le joueur peut passer au niveau suivant !", "blue_bg"))
            level_up()
            

        if Player["inventory"]["Food"] >= 1500 and Player["fork_nb"]:
            send_command("fork")
            Player["fork_nb"] -= 1
            
        if check_capacity():
            fork()
    
        if Debug:
            print(color("Votre position:", "blue"), Player["position"])
        
        mouvements = calculate_best_move()
        for mouv in mouvements :
            send_command(mouv)
        update_map_with_vision()

