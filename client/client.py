import socket
import sys
import argparse
import json
import random
from color import color

# Variable Globale
Debug = False
Client : socket
Direction = ['N', 'E', 'S', 'W']
Player: dict

ret = [
    {"p":{"x":0,"y":0},"c":[]},
    {"p":{"x":64,"y":34},"c":[{"Food":5}]},
    {"p":{"x":0,"y":34},"c":[{"Food":3}]},
    {"p":{"x":1,"y":34},"c":[{"Food":1}]}]

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
    if Debug: 
        print("Connexion...")
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)
        client.connect((host, port))
    except socket.timeout:
        sys.stderr.write("Timeout: Connexion au serveur expirée\n")
        sys.exit(1)
    except ConnectionRefusedError:
        sys.stderr.write("Erreur de connexion: Connexion refusée\n")
        sys.exit(1)
    if Debug:
        print(f"Connexion vers {host}:{port} reussie.")
    client.send("".encode())
    print(client.recv(1024).decode())
    client.send((team + '\n').encode())
    connexion_and_map_size =  client.recv(1024)
    if connexion_and_map_size.decode() == f"The team {team} does not exist\n":
        sys.stderr.write(connexion_and_map_size.decode())
        sys.exit(1)
    global Client
    Client = client
    return connexion_and_map_size.decode()

def init(hostname, port, team): 
    connexion_and_map_size = server_connexion(hostname, port, team)
    global Player
    Player = {}
    Player["direction"] = 'N'
    connexion_and_map_size = connexion_and_map_size.split('\n')
    Player["connexion"] = connexion_and_map_size[0]
    Player["map_size"] = tuple(map(int, connexion_and_map_size[1].split()))
    Player["map"] = [[{} for x in range(Player["map_size"][0])] for y in range(Player["map_size"][1])]

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
    vision_data = send_command("voir")
    vision_data = json.loads(vision_data)
    get_player_position(vision_data)
    for tile in vision_data:
        position = (tile["p"]["x"], tile["p"]["y"])
        content = {k: v for d in tile["c"] for k, v in d.items()}
        content = {**content, **tile["p"]}
        update_tile_content(content)
        Player["map"][position[1]][position[0]] = content
    

def print_map(map):
    print("Carte:")
    for i, row in enumerate(map):
        print(i, row)

def send_command(*args):
    command = " ".join(args)
    Client.send((command + '\n').encode())
    try : 
        response = Client.recv(1024).decode()
    except socket.timeout:
        sys.stderr.write("Tu es mort\n")
        sys.exit(0)
    if response == "You died\n":
        sys.stderr.write("Tu es mort\n")
        sys.exit(0)
    if Debug:
        print(f"{color(command, "red")} : {color(" ".join(response.split()), "lightgreen")}")
    return response

def calculate_moves(x_dest, y_dest):
    moves = []
    x, y, direction = Player["position"][0], Player["position"][0], Player["direction"]
    print(color("calculate_moves:", "purple"), x, y, x_dest, y_dest, direction)
    # Bouger horizontalement
    while x != x_dest:
        
        # print("calculate_moves", x, y, x_dest, y_dest, direction)
        # Déplacer vers l'est
        if x_dest > x: # Si tu dois aller a droite
            if direction == 'N':
                moves.append("droite")
                direction = 'E'
            elif direction == 'E':
                moves.append("avance")
                x += 1
            elif direction == 'S':
                moves.append("gauche")
                direction = 'E'
            elif direction == 'W':
                moves.append("gauche")
                moves.append("gauche")
                direction = 'E'
        # Déplacer vers l'ouest
        elif x_dest < x: # Si tu dois aller a gauche
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
            elif direction == 'W':
                moves.append("avance")
                x -= 1

    # Bouger verticalement
    while y != y_dest:
        # print("calculate_moves", x, y, x_dest, y_dest, direction)

        # Déplacer vers le nord
        if y_dest < y: 
            if direction == 'N':
                moves.append("avance")
                y -= 1
            elif direction == 'E':
                moves.append("gauche")
                direction = 'N'
            elif direction == 'S':
                moves.append("droite")
                moves.append("droite")
                direction = 'N'
            elif direction == 'W':
                moves.append("droite")
                direction = 'N'
        # Déplacer vers le sud
        elif y_dest > y:
            if direction == 'N':
                moves.append("droite")
                moves.append("droite")
                direction = 'S'
            elif direction == 'E':
                moves.append("droite")
                direction = 'S'
            elif direction == 'S':
                moves.append("avance")
                y += 1
            elif direction == 'W':
                moves.append("gauche")
                direction = 'S'
    Player["direction"] = direction
    return moves

def prendre(consommables):
    while consommables:
        items = [i for i in consommables]
        focus_items = random.choices(items, k=1)[0]
        send_command(f"prend {focus_items}")
        consommables[focus_items] -= 126 if focus_items == "Food" else 1
        if consommables[focus_items] <= 0:
            del consommables[focus_items]
        if Debug:
            print(color("Reste sur case:", "purple"), consommables)

def calculate_best_move():
    # Liste des positions adjacentes
    adjacent_positions = [row for col in Player["map"] for row in col if row]
    max_score = float('-inf')
    best_moves = []
    
    for case in adjacent_positions:
        consommable = {key: item for key, item in case.items() if key not in ['x', 'y', 'Player']}
        score = sum(consommable.values())
        if score > max_score and score > 0 and consommable:
            best_moves = [case["x"], case["y"]]
            max_score = score
    # Calculer les mouvements pour atteindre la meilleure position
    if best_moves:
        if best_moves == [Player["position"][0], Player["position"][1]]:
            if Debug:
                print(f"{color("Same place", "red_bg")}", consommable)
            prendre(consommable)
        return calculate_moves(best_moves[0], best_moves[1])
    else:
        if Debug:
            print(f"{color("Avance random", "red_bg")}", Player["direction"], "\n",adjacent_positions)
        # Si aucune position adjacente n'a de ressources, rester sur place
        direction = random.choices(['avance', 'droite', 'gauche'], weights=[0.5, 0.25, 0.25], k=1)[0]
        if direction == "droite":
            Player["direction"] = Direction[(Direction.index(Player["direction"]) + 1) % 4]
        elif direction == "gauche":
            Player["direction"] = Direction[Direction.index(Player["direction"]) - 1]
        if Debug:
            print(f"random : {direction}\nnouvelle direction : {Player["direction"]}")
        update_map_with_vision()
        return [direction]

def main():
    args = parser()
    # Initialisation du joueur
    init(args.hostname, args.port, args.team)
    
    # Mettre à jour la carte avec la vision
    update_map_with_vision()
    
    if Debug:
        print("Player init:")
        for i in Player:
            print("\t", i)
    
    while True :
        # Demander la vision au serveur
        response = send_command("inventaire")
        print(color("Votre position:", "blue"), Player["position"])
        
        mouvements = calculate_best_move()
        print(mouvements)
        for mouv in mouvements :
            send_command(mouv)
        # print("Mouvements:", moves)
        # print("Nouvelle direction:", new_direction)
        
    
    # Afficher la carte
    # print_map(map)

