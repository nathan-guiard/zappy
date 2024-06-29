import socket
import argparse
import json
import random
from color import color
import copy
import multiprocessing
import signal
import sys
from datetime import datetime


# Variable Globale
Debug : bool
Client : socket
Direction = ['N', 'E', 'S', 'W']
Player: dict
list_processus: multiprocessing.Process

levels = {
        1: {"Player":1, "Linemate": 1},
        2: {"Player":2, "Linemate": 1, "Deraumere": 1, "Sibur": 1},
        3: {"Player":2, "Linemate": 2, "Sibur": 1, "Phiras": 2},
        4: {"Player":4, "Linemate": 1, "Deraumere": 1, "Sibur": 2, "Phiras": 1},
        5: {"Player":4, "Linemate": 1, "Deraumere": 2, "Sibur": 1, "Mendiane": 3},
        6: {"Player":6, "Linemate": 1, "Deraumere": 2, "Sibur": 3, "Phiras": 1},
        7: {"Player":6, "Linemate": 2, "Deraumere": 2, "Sibur": 2, "Mendiane": 2, "Phiras": 2, "Thystame": 1},
}

def parser():
    """Parse et check les arguments

    Returns:
        Namespace: contient les arguments 
    """
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
    """Connection au serveur

    Args:
        host (string): _description_
        port (string): _description_
        team (string): _description_

    Returns:
        _type_: _description_
    """
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
    response = Client.recv(4096).decode()
    print(response)
    Client.send((team + '\n').encode())
    response: str = Client.recv(4096).decode()
    if response.endswith == "does not exist\n":
        sys.stderr.write(response)
        Client.close()
        sys.exit(1)
    elif response.startswith("0\n"):
        sys.stderr.write(f"The team {team} is full\n")
        Client.close()
        sys.exit(1)
    return response

def init(args, id): 
    """Initialise les variables et se connecte au serveur

    Args:
        args (Namespace): contient les arguments (hostname, port et team)
        id (int): Id du joueur
    """
    connexion_and_map_size = server_connexion(args.hostname, args.port, args.team)
    global list_processus, Player_id
    list_processus = []
    Player_id = id
    global Player
    Player = {}
    Player["direction"] = 'N'
    connexion_and_map_size = connexion_and_map_size.split('\n')
    Player["connexion"] = connexion_and_map_size[0]
    Player["map_size"] = tuple(map(int, connexion_and_map_size[1].split()))
    print("map size: ", Player["map_size"])
    Player["map"] = [[{} for x in range(Player["map_size"][0])] for y in range(Player["map_size"][1])]
    Player["level"] = 1
    Player["fork_nb"] = 2 - Player_id if Player_id < 2 else 0
    Player["nb_in_same_pos"] = 1
    Player["same_lvl"] = []

def get_player_position(vision_data):
    if vision_data and len(vision_data) and isinstance(vision_data[0], dict) and "p" in vision_data[0]:
        # Mettre à jour la position du joueur
        Player["position"] = (vision_data[0]["p"]["x"], vision_data[0]["p"]["y"])
        # print(vision_data)

def update_tile_content(content):
    if "Player" in content:
        content["Player"] -= 1
        if content["Player"] == 0:
            del content["Player"]

def update_map_with_vision(priority=True):
    try:
        # [{"p":{"x":22,"y":27},"c":[{"Linemate":1},{"Deraumere":1},{"Sibur":1}]},{"p":{"x":21,"y":26},"c":[{"Food":2}]},{"p":{"x":22,"y":26},"c":[{"Food":1}]},{"p":{"x":23,"y":26},"c":[{"Food":2}]}]
        vision_data = send_command("voir", priority=True)
        vision_data = json.loads(vision_data)
        get_player_position(vision_data)
        for tile in vision_data:
            position = (tile["p"]["x"], tile["p"]["y"])
            content = {k: v for d in tile["c"] for k, v in d.items()}
            content = {**content, **tile["p"]}
            update_tile_content(content)
            Player["map"][position[1]][position[0]] = content
    except json.JSONDecodeError or KeyError as e:
        sys.stderr.write(f"Erreur JSON lors de la mise à jour de la carte avec la vision : {e}\n")

def broadcast_go(direction):
    """Se deplace vers l'emetteur du broadcast

    Args:
        direction (int): Direction de l'emetteur

    Returns:
        bool: True si on arrive, False autrement
    """
    match direction:
        case 1: 
            send_command("avance", priority=True)
        case 2: 
            send_command("avance", priority=True)
            send_command("gauche", priority=True)
            Player["direction"] = Direction[Direction.index(Player["direction"]) - 1]
            send_command("avance", priority=True)
        case 3:
            send_command("gauche", priority=True)
            Player["direction"] = Direction[Direction.index(Player["direction"]) - 1]
            broadcast_go(1)
        case 4:
            send_command("gauche", priority=True)
            Player["direction"] = Direction[Direction.index(Player["direction"]) - 1]
            broadcast_go(2)
        case 5:
            send_command("gauche", priority=True)
            Player["direction"] = Direction[Direction.index(Player["direction"]) - 1]
            send_command("gauche", priority=True)
            Player["direction"] = Direction[Direction.index(Player["direction"]) - 1]
            broadcast_go(1)
        case 6:
            send_command("droite", priority=True)
            Player["direction"] = Direction[(Direction.index(Player["direction"]) + 1) % 4]
            broadcast_go(8)
        case 7:
            send_command("droite", priority=True)
            Player["direction"] = Direction[(Direction.index(Player["direction"]) + 1) % 4]
            broadcast_go(1)
        case 8:
            send_command("avance", priority=True)
            send_command("droite", priority=True)
            Player["direction"] = Direction[(Direction.index(Player["direction"]) + 1) % 4]
            send_command("avance", priority=True)
        case 0:
            return True # Je suis sur la case en question
    return False

def wait_incantation_finish():
    """Attend le message de fin d'incantation
    Il receptionne les reponses serveur
    
    Returns:
        bool: True si l'incantation est fini, False autrement
    """
    try:
        response:str = Client.recv(4096).decode()
    except socket.timeout or ConnectionResetError or BrokenPipeError:
        sys.stderr.write("Tu es mort\n")
        wait_and_exit()
    if response.startswith("You died"):
        sys.stderr.write(response)
        wait_and_exit()
    elif response.startswith("End of game"):
        print(end=response)
        wait_and_exit()
    elif response.startswith("Disconnected"):
        print(end=response)
        wait_and_exit()
    print(end=f"    ID:{Player_id} || attente : " + response)
    if response.startswith("broadcast") and response.endswith("finish\n"):
        response = response.split()
        direction = int(response[1][:response[1].find(':')])
        if direction == 0:
            return True
    return False

def help_incantation():
    try:
        beacon = send_command("beacon", priority=True)
        beacon = json.loads(beacon)
                        # [{"x":11,"y":32}]
        if not len(beacon):
            return False
        beacon = beacon[0]
    except json.JSONDecodeError as e:
        # sys.stderr.write(f"Erreur JSON lors de la mise à jour de la carte avec la vision : {e}\n")
        return False

    # Cense envoye beacon et recuperer les coords
    x_dest = int(beacon["x"])
    y_dest = int(beacon["y"])
    
    update_map_with_vision(priority=True)
    mouvements = calculate_moves(x_dest, y_dest)
    # Chaque mouvements met 7 tours et j'appelle voir avant cela et une fois arrive je dois lancer incantation
    # if not (len(mouvements) + 1) * 7 < 300: # Si trop loin
        # return
    for mouv in mouvements :
        send_command(mouv, priority=True)
    level_up(join=True)
    update_map_with_vision(priority=True)
    update_inventory()
    return True
    

def manage_broadcast(command:str, response:str, priority: bool):
    response = response.split()
    if len(response) < 3:
        return
    
    direction, messages = int(response[1][:response[1].find(':')]), response[2:]
    broadcast_param = ["command", "level", "detail", "pid"]
    broadcast = {broadcast_param[index]: messages[index] for index in range(min(len(broadcast_param), len(messages)))}
    
    # print(f"ID:{Player_id} || {color(f'interupt {command}', 'pink')} {color(f'receive', 'darkgrey')} : {color(' '.join(response), 'lightgrey')}{color(f' {priority}', 'blue') if priority else ''} {datetime.now().strftime('%H:%M:%S.%f')}")

    if broadcast["command"] == "incantation":
        if int(broadcast["level"]) == Player["level"]:
            if broadcast["detail"] == "info":
                send_command(f'broadcast incantation {Player["level"]} myinfo {multiprocessing.current_process().pid}', priority=True)
            elif broadcast["detail"] == "myinfo":
                if broadcast["pid"] not in Player["same_lvl"]:
                    Player["same_lvl"].append(broadcast["pid"])

    if not priority and broadcast["command"] == "incantation":
        if int(broadcast["level"]) == Player["level"] and int(broadcast["level"]) > 1:
            # Broadcast +1 joueur pret a incanter
            if broadcast["detail"] == "waiting":
                help_incantation()
        pass 


def broadcast_gestion(command: str, response: str, priority:bool):
    """Gestion des appels a broadcast

    Args:
        command (str): Commande ayant ete intercepte par le broadcast
        response (str): Reponse contenant le broadcast
        priority (bool): Permet d'empecher la creation d'un processus broadcast.

    Returns:
        str: Reponse avant interruption par le broadcast
    """
    # Permet de recuperer la reponse de la commande interceptee
    command_response = send_command(command, priority=True, block_send=True)
    manage_broadcast(command, response, priority)
    return command_response

def send_command(command: str, priority:bool = False, block_send:bool = False) -> str:
    """Envoi une commande au serveur
    Il peut se faire ecraser par un processus broadcast si un broadcast est recu au moment de la reponse de la commande
    Args:
        command (string): Commande envoyee
        command_priority (bool, optional): Permet d'empecher la creation d'un processus broadcast. Defaults to False.

    Returns:
        str: Reponse du serveur
    """
    # print(command, "broad", in_broadcast, "priority", command_priority)
    try:
        if not block_send:
            Client.send((command + '\n').encode())
        response:str = Client.recv(4096).decode()
    except socket.timeout or ConnectionResetError or BrokenPipeError:
        sys.stderr.write("Tu es mort\n")
        wait_and_exit()
        
    # if response.count("\n") > 1:
    #     a = response.count("\n")
    #     print(f"{a}  {Player['level']}   ID:{Player_id} || {color(command, 'red_bg')} : {response}")
    responses = response.strip().split('\n')
    official_response = None
    broadcasts = []

    if len(responses) > 2:
        print(responses)

    for resp in responses:
        if resp.startswith("broadcast"):
            broadcasts.append(resp)
        else:
            if official_response is not None:
                print(f"{color('houlalalalalalalalal', 'red_bg')}  {resp}   {official_response}")
            official_response = resp
    
    if official_response is None:
        return
    
    if command == "gauche" and official_response.startswith("ok"):
        Player["direction"] = Direction[Direction.index(Player["direction"]) - 1]
    elif command == "droite" and official_response.startswith("ok"):
        Player["direction"] = Direction[(Direction.index(Player["direction"]) + 1) % 4]
    if official_response.startswith("You died"):
        sys.stderr.write(response)
        wait_and_exit()
    elif official_response.startswith("End of game"):
        print(end=response)
        wait_and_exit()
    elif official_response.startswith("Disconnected"):
        print(end=response)
        wait_and_exit()
    
    # if not priority:
    #     print(f"ID:{Player_id} || {color(command, 'red')} : {color(' '.join(response.split()), 'lightgreen')} {datetime.now().strftime('%H:%M:%S.%f')}")
    # else :
    #     print(f"ID:{Player_id} || {color(command, 'red')} : {color(' '.join(response.split()), 'lightgreen')} {datetime.now().strftime('%H:%M:%S.%f')}")

    Player["file"].write(f"ID:{Player_id} || {command} : {' '.join(response.split())} {datetime.now().strftime('%H:%M:%S.%f')}\n")
    print(f"ID:{Player_id} || {color(command, 'red')} : {color(' '.join(response.split()), 'lightgreen')} {datetime.now().strftime('%H:%M:%S.%f')}")

    # if Player["level"] > 2:
        # print(f"ID:{Player_id} {Player['level']} || {color(command, 'lightred')} : {color(' '.join(response.split()), 'lightgreen')} {datetime.now().strftime('%H:%M:%S.%f')}")

    return official_response

def calculate_moves(x_dest, y_dest):
    """
    Cree la liste des commandes permettant d'arrive a destination
    Args:
        x_dest (int): destination x
        y_dest (int): destination y

    Returns:
        list: contient la liste de mouvements
    """
    def wrapped_distance(a, b, size):
        """Permet de preferer un tour de la carte plutot que traverser toute la carte

        Args:
            a (int): coordonne 
            b (int): coordonne
            size (int): taille de la carte

        Returns:
            int: La decision la plus optimisee
        """
        choix = ((a - b) % size, (b - a) % size)
        return -1 if choix.index(min(choix)) == 0 else 1, min(choix)
    moves = []
    x, y, direction = Player["position"][0], Player["position"][1], Player["direction"]
    if Debug:
        print(color("calculate_moves:", "purple"), x, y, x_dest, y_dest, direction)
    
    direction_x, distance_x = wrapped_distance(x, x_dest, Player["map_size"][0])
    direction_y, distance_y = wrapped_distance(y, y_dest, Player["map_size"][1])
    
    # Bouger verticalement
    while distance_y:
        if direction_y == -1:  #monter
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
        elif direction_y == 1: #descendre
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
        if direction_x == -1:  #gauche
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
        elif direction_x == 1: #droite
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
    return moves

def prendre(consommables, x, y):
    """Envoi la commande prendre au serveur et met a jour la carte en consequence
    Si un echec survient, la mise a jour de la carte a lieu
    
    Args:
        consommables (dict): contient les ressources de la case
        x (int): coordonne x
        y (int): coordonne y
    """
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
    

def calculate_remaining_needs():
    """Calcule les besoins restants pour passer au niveau suivant."""
    level = Player["level"]
    inventory = Player["inventory"]
    next_level_requirements = levels[level]

    remaining_needs = {}
    for resource, required_quantity in next_level_requirements.items():
        if resource != "Player":
            current_quantity = inventory.get(resource, 0)
            remaining_quantity = max(required_quantity - current_quantity, 0)
            remaining_needs[resource] = remaining_quantity
    return remaining_needs

def score_by_level(consommable: dict, food_threshold: int = 150): 
    """Attribue un score en fonction des ressources trouvées.

    Args:
        consommable (dict): Contient les items d'une case, ainsi que leurs quantités.
        food_threshold (int, optional): Seuil au-delà duquel le coefficient de nourriture est réduit. Default to 50.

    Returns:
        int: Score.
    """
    inventory = Player["inventory"]
    remaining_needs = calculate_remaining_needs()

    # Réguler les coefficients des ressources en fonction des besoins restants
    resource_coefficients = {}
    for resource, remaining_quantity in remaining_needs.items():
        if remaining_quantity > 0:
            resource_coefficients[resource] = 10 / remaining_quantity  # Exemple de régulation
        else:
            resource_coefficients[resource] = 0

    # Réduire le coefficient de la nourriture si elle dépasse le seuil
    if inventory.get("Food", 0) >= food_threshold:
        resource_coefficients["Food"] = 0.1  # Réduire significativement la priorité de la nourriture
    else:
        resource_coefficients["Food"] = 1

    # Calculer le score en tenant compte des coefficients régulés
    score = sum(quantity * resource_coefficients.get(resource, 0)
                for resource, quantity in consommable.items())

    return score


def calculate_best_move():
    """Calcule la liste des mouvements vers le filon de ressources le plus interessant

    Returns:
        list: Contient tous les mouvements pour arriver au filon
    """
    # Liste des positions adjacentes
    adjacent_positions = [row for col in Player["map"] for row in col if row]
    max_score = float('-inf')
    best_moves = []
    
    # if Debug:
    #     map_print(adjacent_positions, Player["position"][0], Player["position"][1], Player["map_size"][0], Player["map_size"][1])
    
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
    """Met a jour l'inventaire (un envoi de commande est fait)
    """
    response = send_command("inventaire")
    inventory_data = json.loads(response)
    # print(f"{color('Inventaire', 'orange')} {Player['level']}: {color(' '.join(response.split()), 'lightgrey')}")
    Player["inventory"] = {}
    for item in inventory_data:
        for key, value in item.items():
            Player["inventory"][key] = value
    

def check_level_requirements():
    """Check si les besoins sont satisfaits
    Des envois de broadcast sont fait s'il manque que des joueurs

    Returns:
        bool: True si c'est le cas, False autrement
    """
    if Player["level"] == 8:
        return False
    requirements = levels[Player["level"]]
    for item, quantity in requirements.items():
        if item == "Player":
            continue
        elif item not in Player["inventory"]:
            return False
        elif Player["inventory"][item] < quantity:
            return False
    if Player["level"] == 1:
        return True
    if not len(Player["same_lvl"]) < requirements["Player"]:
        return False
    # Faire un check du nombre de joueur du meme niveau que moi dans la map et voir si il y en a assez de present du meme niveau que moi
    # Et False dans le cas contraire
    return True

def level_up(join = False):
    """Procede au level up (depose les items et incante)
    Si le processus echoue, la vision et l'inventaire seront mis a jour
    """
    if not join:
        requirements = levels[Player["level"]]
        for item, quantity in requirements.items():
            if item == "Player":
                continue
            for _ in range(quantity):
                send_command(f"pose {item}", priority=True)
            Player["inventory"][item] -= quantity
            if not Player["inventory"][item]:
                del Player["inventory"][item]
        
    send_command(f"broadcast incantation {Player['level']} waiting {multiprocessing.current_process().pid} {Player['position'][0]} {Player['position'][1]}", priority=True)
    response = send_command("incantation", priority=True)
    if response.startswith("ko"):
        update_map_with_vision(priority=True)
        update_inventory()
        return
    
    Player["level"] += 1
    Player["same_lvl"] = []
    Player["fork_nb"] = 0
    send_command(f"broadcast incantation {Player['level']} levelup {multiprocessing.current_process().pid}", priority=True)
    print(color(f"ID:{Player_id} || Succesfully level up {Player['level']}", "blue"))
    if not help_incantation():
        send_command(f"broadcast incantation {Player['level']} info", priority=True)
    
def check_capacity(have_fork):
    """check la capacite de joindre fork le programme et rejoindre la session avec un autre joueur
    Elle necessite le succes d'un fork au prealable 

    Args:
        have_fork (bool): Represente si un fork a reussi au prealable

    Returns:
        boolean: True si un fork du programme est possible, False autrement
    """
    if not have_fork:
        return False
    return int(send_command("connect")) > 0

def fork():
    nouveau_processus = multiprocessing.Process(target=main, args=(Player_id + 1,))
    nouveau_processus.start()
    nouveau_processus.join(timeout=0.2)
    if not nouveau_processus.is_alive():
        print(color("Process est pas cree", "red_bg"))
        return False
    list_processus.append(nouveau_processus)
    Player["fork_nb"] -= 1
    return True

def wait_and_exit():
    for nouveau_processus in list_processus:
        nouveau_processus.join()
    Client.close()
    sys.exit(0)

def sigint_handler(signal, frame):
    if Player_id == 0:
        print("SIGINT reçu, fermeture du client")
    for nouveau_processus in list_processus:
        nouveau_processus.join()
    Client.close()
    sys.exit(0)

def main(id: int = 0, args=None):
    args = parser()
    # Initialisation du joueur
    init(args, id)
    signal.signal(signal.SIGINT, sigint_handler)
    
    
    filename = f"{multiprocessing.current_process().pid}_{args.team}_{Player_id}.txt"
    file = open(filename, 'w')
    Player["file"] = file
    
    have_fork = False
    while True :
        update_map_with_vision()
        update_inventory()
        
        if check_level_requirements():
            if Debug:
                print(color("Le joueur peut passer au niveau suivant !", "blue_bg"))
            level_up()
        
        # Fork le programme si les conditions sont réunies
        if Player["fork_nb"] > 0 and not have_fork and Player["inventory"]["Food"] >= 1750:
            send_command("fork")
            have_fork = True
        if check_capacity(have_fork):
            if fork():
                have_fork = False

        mouvements = calculate_best_move()
        for mouv in mouvements :
            send_command(mouv)
            
