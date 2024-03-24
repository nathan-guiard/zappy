import socket
from client_lib import Player
import sys
import argparse
import json
import random

# Variable Globale
Debug = False
Direction = ['N', 'E', 'S', 'W']

ret = [
    {"p":{"x":0,"y":0},"c":[]},
    {"p":{"x":64,"y":34},"c":[{"Food":5}]},
    {"p":{"x":0,"y":34},"c":[{"Food":3}]},
    {"p":{"x":1,"y":34},"c":[{"Food":1}]}]

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
    return client, connexion_and_map_size.decode()


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

def init(connexion_and_map_size): 
    connexion_and_map_size = connexion_and_map_size.split('\n')
    connexion = connexion_and_map_size[0]
    x, y = map(int, connexion_and_map_size[1].split())
    return connexion, (x, y)

def get_player_position(vision_data):
    if vision_data and isinstance(vision_data[0], dict) and "p" in vision_data[0]:
        # Mettre à jour la position du joueur
        return (vision_data[0]["p"]["x"], vision_data[0]["p"]["y"])
    return None

def update_tile_content(content):
    if "Player" in content:
        content["Player"] -= 1
        if content["Player"] == 0:
            del content["Player"]

def update_map_with_vision(map, vision_data):
    for tile in vision_data:
        position = (tile["p"]["x"], tile["p"]["y"])
        content = {k: v for d in tile["c"] for k, v in d.items()}
        content = {**content, **tile["p"]}
        update_tile_content(content)
        map[position[1]][position[0]] = content

def print_map(map):
    print("Carte:")
    for i, row in enumerate(map):
        print(i, row)

def send_command(client, command):
    client.send(command.encode())
    response = client.recv(1024).decode()
    print(response)



def calculate_moves(x, y, x_dest, y_dest, direction):
    moves = []
    print("calculate_moves", x, y, x_dest, y_dest, direction)
    # Bouger horizontalement
    while x != x_dest:
        
        # print("calculate_moves", x, y, x_dest, y_dest, direction)
        # Déplacer vers l'est
        if x_dest > x: # Si tu dois aller a droite
            if direction == 'N':
                moves.append("droite\n")
                direction = 'E'
            elif direction == 'E':
                moves.append("avance\n")
                x += 1
            elif direction == 'S':
                moves.append("gauche\n")
                direction = 'E'
            elif direction == 'W':
                moves.append("gauche\n")
                moves.append("gauche\n")
                direction = 'E'
        # Déplacer vers l'ouest
        elif x_dest < x: # Si tu dois aller a gauche
            if direction == 'N':
                moves.append("gauche\n")
                direction = 'W'
            elif direction == 'E':
                moves.append("gauche\n")
                moves.append("gauche\n")
                direction = 'W'
            elif direction == 'S':
                moves.append("droite\n")
                direction = 'W'
            elif direction == 'W':
                moves.append("avance\n")
                x -= 1

    # Bouger verticalement
    while y != y_dest:
        # print("calculate_moves", x, y, x_dest, y_dest, direction)

        # Déplacer vers le nord
        if y_dest < y: 
            if direction == 'N':
                moves.append("avance\n")
                y -= 1
            elif direction == 'E':
                moves.append("gauche\n")
                direction = 'N'
            elif direction == 'S':
                moves.append("droite\n")
                moves.append("droite\n")
                direction = 'N'
            elif direction == 'W':
                moves.append("droite\n")
                direction = 'N'
        # Déplacer vers le sud
        elif y_dest > y:
            if direction == 'N':
                moves.append("droite\n")
                moves.append("droite\n")
                direction = 'S'
            elif direction == 'E':
                moves.append("droite\n")
                direction = 'S'
            elif direction == 'S':
                moves.append("avance\n")
                y += 1
            elif direction == 'W':
                moves.append("gauche\n")
                direction = 'S'
    return moves, direction

def prendre(consommables, client):
    while consommables :
        items = [i for i in consommables]
        focus_items = random.choices(items, k=1)[0]
        send_command(client, f"prend {focus_items}\n")
        consommables[focus_items] -= 126 if focus_items == "Food" else 1
        
def calculate_best_move(map, x, y, direction, client):
    # Liste des positions adjacentes
    adjacent_positions = [row for col in map for row in col if row]
    max_score = float('-inf')
    best_moves = []
    
    for case in adjacent_positions:
        consommable = {key: item for key, item in case.items() if key not in ['x', 'y', 'Player']}
        score = sum(consommable.values())
        print(score)
        if score > max_score :
            best_moves = [case["x"], case["y"]]
            max_score = score
    # Calculer les mouvements pour atteindre la meilleure position
    if best_moves:
        if best_moves == [x, y]:
            print("Same place")
            prendre(consommable, client)
        return calculate_moves(x, y, best_moves[0], best_moves[1], direction)
    else:
        # Si aucune position adjacente n'a de ressources, rester sur place
        direction = random.choices(['avance', 'droite', 'gauche'], weights=[0.5, 0.25, 0.25], k=1)[0]
        return [f"{direction}\n"], direction 



def main():
    args = parser()
    client, start_player = server_connexion(args.hostname, args.port, args.team)
    
    # Initialisation du joueur
    player = {}
    player["connexion"], map_size = init(start_player)
    player["direction"] = 'N'  # Direction initiale
    
    map = [[{} for x in range(map_size[0])] for y in range(map_size[1])]
    
    # Demander la vision au serveur
    command = "voir\n"
    client.send(command.encode())
    response = client.recv(1024).decode()
    print(response)
    
    # Analyser la vision
    vision_data = json.loads(response)
    
    # Mettre à jour la position du joueur
    player_position = get_player_position(vision_data)
    if player_position:
        print("Votre position:", player_position)
        player["position"] = player_position
    
    # Mettre à jour la carte avec la vision
    update_map_with_vision(map, vision_data)
    
    
    mouvements, player["direction"] = calculate_best_move(map, player_position[0], player_position[1], player["direction"], client)
    print(mouvements)
    for mouv in mouvements :
        send_command(client, mouv)
    # print("Mouvements:", moves)
    # print("Nouvelle direction:", new_direction)
    
    # Afficher la carte
    # print_map(map)



"""
# command = "avance\n"
# client.send(command.encode())
# response = client.recv(1024).decode()
# print(f"{command} : {response}")
# command = "droite\n"
# client.send(command.encode())
# response = client.recv(1024).decode()
# print(f"{command} : {response}")
# command = "avance\n"
# client.send(command.encode())
# response = client.recv(1024).decode()
# print(f"{command} : {response}")


# command = "voir\n"
# client.send(command.encode())
# response = client.recv(1024).decode()
# print(f"{command} : {response}")

# command = "gauche\n"
# client.send(command.encode())
# response = client.recv(1024).decode()
# print(f"{command} : {response}")

# command = "avance\n"
# client.send(command.encode())
# response = client.recv(1024).decode()
# print(f"{command} : {response}")

# command = "voir\n"
# client.send(command.encode())
# response = client.recv(1024).decode()
# print(f"{command} : {response}")

# player["vision"] = {}
# while True:
#     # Vérifier s'il n'y a pas d'informations dans la vision du joueur
#     if not player["vision"]:
#         client.send("voir\n".encode())
#         vision_response = client.recv(1024).decode()
#         player["vision"] = json.loads(vision_response)

#     # Avancer vers une case contenant des ressources
#     next_position = None
#     for case in player["vision"]:
#         if case["c"]:
#             next_position = (case["p"]["x"], case["p"]["y"])
#             break

#     if next_position:
#         # Envoyer une commande pour avancer vers la prochaine position
#         command = "avance\n"
#         client.send(command.encode())
#         response = client.recv(1024).decode()
#         print(response)  # Afficher la réponse du serveur

#         # Mettre à jour la position du joueur
#         player["x"], player["y"] = next_position
#         # Afficher la nouvelle position du joueur
#         print(f"Le joueur est maintenant à la position ({player['x']}, {player['y']})")

#         # Réinitialiser la vision du joueur pour demander de nouveaux informations
#         player["vision"] = {}
#     else:
#         print("Aucune case contenant des ressources n'a été trouvée.")
#         break  # Sortir de la boucle principale si aucune case n'est trouvée

#     # Ajouter plus de logique ici selon les besoins"""