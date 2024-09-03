import socket
import json
import argparse
import multiprocessing
from states.state import Idle

connexion_error = "Erreur : la connexion au serveur n'est pas établie."
Direction = ['N', 'E', 'S', 'W']


class Player:
    """Classe principale pour le joueur."""
    
    def __init__(self, hostname, port, team_name):
        self.hostname = hostname
        self.port = port
        self.view = {}
        self.id = multiprocessing.current_process().pid
        self.socket = None
        self.timeout = 5
        self.inventory = {
            "Food": 0,
            "Linemate": 0,
            "Deraumere": 0,
            "Sibur": 0,
            "Mendiane": 0,
            "Phiras": 0,
            "Thystame": 0
        }
        self.num_players = 0
        self.coordinates = (0, 0)
        self.direction = Direction[0]
        self.map_size = (0, 0)
        self.team_name = team_name
        self.level = 1
        self.focus_ressources = None
        self.focus_coords = None
        self.communication = []
        self.have_fork = False
        self.list_processus = []
        # self.memory = {
            # player_id: {linemate: 0, deraumere: 0, sibur: 0, mendiane: 0, phiras: 0, thystame: 0, level:1, team: "team_name"}
        # }
        self.memory = {}
        self.state = Idle(self)  # Débuter en état Idle
        
        self.connect_to_server()
        self.inventaire()
        self.voir()
        self.display_info()
        
        self.state.enter_state()
        self.routine()
        
    def connect_to_server(self):
        try:
            print(f"Tentative de connexion au serveur {self.hostname}:{self.port}...")
            
            # Crée un socket TCP/IP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Définit un timeout pour la connexion
            self.socket.settimeout(self.timeout)
            
            # Tente de se connecter au serveur
            self.socket.connect((self.hostname, self.port))
            print(f"Connexion établie avec le serveur {self.hostname}:{self.port}")
            
            # Recevoir le message de bienvenue
            welcome_message = self.socket.recv(1024).decode('utf-8')
            print(f"Message reçu du serveur : {welcome_message}")
            
            if "BIENVENUE" in welcome_message:
                # Envoyer le nom de l'équipe
                self.socket.sendall(f"{self.team_name}\n".encode('utf-8'))
                print(f"Nom de l'équipe '{self.team_name}' envoyé au serveur.")
                
                 # Recevoir la réponse du serveur après l'envoi du nom d'équipe
                response = self.socket.recv(1024).decode('utf-8').strip()
                if "does not exist" in response:
                    self.close_connection(f"Erreur : L'équipe '{self.team_name}' n'existe pas.")
                    return
                
                parts = response.split('\n')
                if len(parts) != 2:
                    self.close_connection("Erreur : format de message du serveur invalide.")
                    return
                
                # Nombre de joueurs
                try:
                    self.num_players = int(parts[0])
                    print(f"Nombre de joueurs dans l'équipe : {self.num_players}")
                except ValueError:
                    self.close_connection("Erreur : Le nombre de joueurs reçu n'est pas valide.")
                    return
                
                # Coordonnées de la carte
                try:
                    self.map_size = tuple(map(int, parts[1].split()))
                    print(f"Coordonnées de la carte reçues : {self.map_size}")
                except ValueError:
                    self.close_connection("Erreur : La taille de la carte reçues n'est pas valide.")
                    return

            else:
                self.close_connection("Erreur de connexion")
                    
        except socket.timeout:
            self.close_connection(f"Connexion échouée : délai d'attente dépassé ({self.timeout} secondes)")
        
        except socket.error as e:
            self.close_connection(f"Erreur lors de la connexion au serveur: {e}")
            
        print("Connexion etablie")
        
    def send_message(self, message, send=True):
        """Envoie un message au serveur via le socket donné et retourne la réponse complète jusqu'à réception du caractère de fin \x04."""
        if self.socket is None:
            print(connexion_error)
            return None
        
        try:
            # Envoie le message au serveur
            if send:
                self.socket.sendall(message.encode('utf-8'))
            
            # Réception des données en plusieurs parties jusqu'à rencontrer \x04
            response = []
            while True:
                part: str = self.socket.recv(1024).decode('utf-8')
                if not part:
                    # Connexion perdue ou fin de transmission inattendue
                    print("Connexion perdue ou transmission incomplète.")
                    return None
                response.append(part)
                
                # Vérifie si le caractère de fin est dans la partie reçue
                if '\x04' in part:
                    break
            
            # Combine les parties reçues en une seule chaîne
            full_response = ''.join(response).strip()
            # Retirer le caractère de fin \x04
            
            full_response = full_response.replace('\x04', '')
            
            response_list = list(filter(None, full_response.split('\n')))
            
            if "You died" in response_list:
                print(full_response)
                print("Player is dead")
                return None
            
            final_response = None
            print(f"response_list: {response_list}")
            for response in response_list:
                if response.startswith("broadcast"):
                    self.communication.append(response.split(' ')[1:])
                else:
                    final_response = response
            
            print(f"communication: {self.communication}")
            if final_response is None:
                return self.send_message("reception", False)
            print(f"final_response: {final_response}")
            return final_response

        except socket.error as e:
            print(f"Erreur lors de l'envoi du message : {e}")
            return None

    def close_connection(self, error_message: str = None):
        if error_message:
            print(error_message)
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Connexion fermée.")
        exit(0)
        
    def inventaire(self):
        """Demande l'inventaire au serveur et le stocke sous forme de dictionnaire."""
        # Envoyer la commande pour demander l'inventaire
        response = self.send_message("inventaire")
        if response is None:
            self.close_connection()
        
        try:
            # Convertir la réponse JSON en dictionnaire
            inventory_data = json.loads(response)
            tile_inventory = inventory_data[0]
            for key, value in tile_inventory.items():
                self.inventory[key] = value
            print(f"Inventaire mis à jour : {self.inventory}")
        except json.JSONDecodeError:
            self.close_connection("Erreur : Impossible de décoder la réponse JSON du serveur.")
        except TypeError:
            self.close_connection("Erreur : Type de données invalide pour l'inventaire.:", response)

    def display_info(self):
        """Affiche les informations du joueur."""
        print("\n--- Informations du Joueur ---")
        print(f"Nom de l'équipe : {self.team_name}")
        print(f"Nombre de joueurs dans l'équipe : {self.num_players}")
        print(f"Coordonnées de la carte : {self.coordinates}")
        print(f"Direction: {self.direction}")
        print(f"Inventaire: {self.inventory}")
        print(f"Memoire: {self.view}")
        print("------------------------------\n")
        
    def routine(self):
        """Boucle principale pour gérer les actions du joueur."""
        while self.socket:
            self.update()  

    def droite(self):
        response = self.send_message("droite")
        if response is None:
            self.close_connection()
        if response != "ok":
            self.close_connection(f"Reponse invalide 'droite': {response}")
        current_index = Direction.index(self.direction)
        self.direction = Direction[(current_index + 1) % len(Direction)]
        # print(f"Réponse du serveur à la commande 'droite' : {response}")

    def gauche(self):
        response = self.send_message("gauche")
        if response is None:
            self.close_connection()
        if response != "ok":
            self.close_connection(f"Reponse invalide 'gauche': {response}")
        current_index = Direction.index(self.direction)
        self.direction = Direction[(current_index - 1) % len(Direction)]
        # print(f"Réponse du serveur à la commande 'gauche' : {response}")


    def avance(self):
        response = self.send_message("avance")
        if response is None:
            self.close_connection()
        if response != "ok":
            self.close_connection(f"Reponse invalide 'avance': {response}")
        if self.direction == 'N':
            self.coordinates = (self.coordinates[0], (self.coordinates[1] - 1) % self.map_size[1])
        elif self.direction == 'E':
            self.coordinates = ((self.coordinates[0] + 1) % self.map_size[0], self.coordinates[1])
        elif self.direction == 'S':
            self.coordinates = (self.coordinates[0], (self.coordinates[1] + 1) % self.map_size[1])
        elif self.direction == 'W':
            self.coordinates = ((self.coordinates[0] - 1) % self.map_size[0], self.coordinates[1])
        # print(f"Réponse du serveur à la commande 'avance' : {response}")


    def voir(self):
        response = self.send_message("voir")
        if response is None:
            self.close_connection()
        
        if response is None:
            self.close_connection(f"Réponse invalide 'voir' : {response}")
            return

        try:
            # Tenter de charger la réponse en tant que JSON
            view_data = json.loads(response)
            # print(f"Réponse du serveur à la commande 'voir' : {view_data}")
        except json.JSONDecodeError:
            # Si la réponse n'est pas un JSON valide, fermer la connexion
            print(f"Erreur JSONDecodeError: La réponse du serveur n'est pas en format JSON : {response}")
            self.close_connection("Réponse invalide 'voir'")
        except TypeError:
            print(f"Erreur TypeError: La réponse du serveur n'est pas en format JSON : {view_data}")
            self.close_connection("Réponse invalide 'voir'")
            
        # Update la position du joueur
        player_tile = view_data[0]
        self.coordinates = (player_tile['p']['x'], player_tile['p']['y'])
        for tile in view_data:
            tile_coords = (tile['p']['x'], tile['p']['y'])
            if tile['c']:
                self.view[tile_coords] = tile['c'][0]
            else:
                self.view[tile_coords] = {}


    def connect(self):
        response = self.send_message("connect")
        if response is None:
            self.close_connection()
        if not response.isdigit():
            self.close_connection(f"Reponse invalide 'connect': {response}")
        return int(response)


    def broadcast(self, message):
        print(f"Broadcasting message: {message}")
        response = self.send_message(f"broadcast {message}")
        if response is None:
            self.close_connection()
        if response != "ok":
            self.close_connection(f"Reponse invalide 'broadcast' : {response}")
        # print(f"Réponse du serveur à la commande 'broadcast' : {response}")


    def fork_manager(self):
        """Suite a la commande fork, si une connexion est possible, visible avec la command connect, alors on peut rajouter un nouveau player"""
        if not self.have_fork:
            return 0
        try:
            # Creation d'un nouveau multiprocessus pour le nouveau joueur
            self.list_processus: multiprocessing.Process
            self.list_processus.append(multiprocessing.Process(target=Player, args=(self.hostname, self.port, self.team_name)))
            self.list_processus[-1].start()
            self.have_fork = False
        except KeyboardInterrupt:
            print("KeyboardInterrupt received, terminating the process...")
            for process in self.list_processus:
                process.terminate()
                process.join()
            print("All processes terminated.")
            self.close_connection("KeyboardInterrupt received, terminating the process...")
        return 0
    
    def fork(self):
        response = self.send_message("fork")
        if response is None:
            self.close_connection()
        if response.startswith("ok"):
            self.have_fork = True
            # print(f"Réponse du serveur à la commande 'fork' : {response}")
            return 0
        elif response.startswith("ko"):
            pass
            # print(f"Réponse du serveur à la commande 'fork' : {response}")
            return 1
        self.close_connection(f"Reponse invalide 'fork': {response}")
            
    
    def incantation(self):
        # Ralonger le socket.timeout
        self.socket.settimeout(self.timeout * 5)
        response = self.send_message("incantation")
        print(f"Réponse du serveur à la commande 'incantation' : {response}")
        self.socket.settimeout(self.timeout)
        if response is None:
            self.close_connection()
        if response.startswith("ok"):
            # print(f"Réponse du serveur à la commande 'incantation' : {response}")
            # print("Level Up")
            self.level += 1
            return 0
        elif response.startswith("ko"):
            # print(f"Réponse du serveur à la commande 'incantation' : {response}")
            return 1
        self.close_connection(f"Reponse invalide 'incantation': {response}")

    def prend(self, ressource):
        response = self.send_message(f"prend {ressource}")
        if response is None:
            self.close_connection(f"Reponse invalide 'prend' : {response}")
            
        ressource = ressource.capitalize()
            
        if response.startswith("ok"):
            # print(f"Réponse du serveur à la commande 'prend' : {response}")
            if ressource == "Food":
                self.inventory[ressource] += 126
            else:
                self.inventory[ressource] += 1
            self.view[self.coordinates][ressource] -= 1
            return 0
        elif response.startswith("ko"):
            self.voir()
            return 1
        else: 
            self.close_connection(f"Reponse invalide 'prend' : {response}")

    def pose(self, ressource):
        response = self.send_message(f"pose {ressource}")
        if response is None:
            self.close_connection()
        
        if response.startswith("ok"):
            self.inventory[ressource] -= 1
            pass
            # print(f"Réponse du serveur à la commande 'pose' : {response}")
        elif response.startswith("ko"):
            self.voir()
        else: 
            self.close_connection(f"Reponse invalide 'pose' : {response}")
        
    

    def update(self):
        """Appelée à chaque cycle de jeu pour mettre à jour l'état."""
        if self.state:
            new_state = self.state.update()
            if new_state:
                self.transition_to(new_state)

    def transition_to(self, new_state):
        """Gère la transition entre états."""
        if self.state:
            self.state.exit_state()
        self.state = new_state
        if self.state:
            self.state.enter_state()
            
    def has_enough_food(self, distance):
        return (distance + 2) * 1.4 < self.inventory["Food"]
    
    def communicate(self):
        for message in self.communication:
            # direction: player_information player_id lvl x y linemate deraumere sibur mendiane phiras thystame
            # Parsing des messages de types : f"Player_information {self.player.id} {self.player.level} {self.player.coordinates} {self.player.inventory}"
            direction = message[0]
            if message[1] == "player_information":
                self.handle_player_information(message[2:])
            
        self.communication = []
        print(f"Memory: {self.memory}")

    def handle_player_information(self, message):
        player_id = message[0]
        player_level = int(message[1])
        player_coordinates = tuple(map(int, message[2:4]))
        player_inventory = {}
        for i in range(4, len(message), 2):
            player_inventory[message[i]] = int(message[i + 1])
        self.memory[player_id] = {
            "level": player_level,
            "coordinates": player_coordinates,
            "inventory": player_inventory
        }






def main():
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
        print("Erreur: Le numéro de port doit être compris entre 1024 et 65535.\n")
        return 1
    
    player = Player("localhost", args.port, args.team)


if __name__ == "__main__":
    main()
