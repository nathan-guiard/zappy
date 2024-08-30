import socket
import json
from states.state import Idle

connexion_error = "Erreur : la connexion au serveur n'est pas établie."
Direction = ['N', 'E', 'S', 'W']


def send_message(sock, message):
    """Envoie un message au serveur via le socket donné et retourne la réponse complète jusqu'à réception du caractère de fin \x04."""
    if sock is None:
        print(connexion_error)
        return None
    
    try:
        # Envoie le message au serveur
        sock.sendall(message.encode('utf-8'))
        
        # Réception des données en plusieurs parties jusqu'à rencontrer \x04
        response = []
        while True:
            part: str = sock.recv(1024).decode('utf-8')
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
        full_response = full_response.removesuffix("\n\x04")
        response_list = list(filter(None, full_response.split('\n')))
        
        if "You died" in response_list:
            print(full_response)
            print("Player is dead")
            return None
        return full_response

    except socket.error as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


class Player:
    def __init__(self, hostname, port, team_name):
        self.hostname = hostname
        self.port = port
        self.view = {}
        self.socket = None
        self.timeout = 5
        self.inventory = {}
        self.num_players = 0
        self.coordinates = (0, 0)
        self.direction = Direction[0]
        self.map_size = (0, 0)
        self.team_name = team_name
        self.level = 1
        self.focus = None
        self.state = Idle(self)  # Débuter en état Idle
        
        self.connect_to_server()
        self.check_inventory()
        self.voir()
        self.display_info()
        
        self.state.enter_state()
        self.routine()
        
        
    def check_inventory(self):
        """Demande l'inventaire au serveur et le stocke sous forme de dictionnaire."""
        if self.socket is not None:
            # Envoyer la commande pour demander l'inventaire
            response = send_message(self.socket, "inventaire")
            
            try:
                # Convertir la réponse JSON en dictionnaire
                inventory_data = json.loads(response)
                self.inventory = inventory_data[0]
                print(f"Inventaire mis à jour : {self.inventory}")
            except json.JSONDecodeError:
                self.close_connection("Erreur : Impossible de décoder la réponse JSON du serveur.")
        else:
            print(connexion_error)


    def connect_to_server(self):
        try:
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


    def close_connection(self, error_message: str = None):
        if error_message:
            print(error_message)
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Connexion fermée.")
        exit(0)


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
        response = send_message(self.socket, "droite")
        if response != "ok":
            self.close_connection(f"Reponse invalide 'droite': {response}")
        current_index = Direction.index(self.direction)
        self.direction = Direction[(current_index + 1) % len(Direction)]
        print(f"Réponse du serveur à la commande 'droite' : {response}")

    def gauche(self):
        response = send_message(self.socket, "gauche")
        if response != "ok":
            self.close_connection(f"Reponse invalide 'gauche': {response}")
        current_index = Direction.index(self.direction)
        self.direction = Direction[(current_index - 1) % len(Direction)]
        print(f"Réponse du serveur à la commande 'gauche' : {response}")


    def avance(self):
        response = send_message(self.socket, "avance")
        if response != "ok":
            self.close_connection(f"Reponse invalide 'avance': {response}")
        print(f"Réponse du serveur à la commande 'avance' : {response}")


    def voir(self):
        response = send_message(self.socket, "voir")
        
        if response is None:
            self.close_connection(f"Réponse invalide 'voir' : {response}")
            return

        try:
            # Tenter de charger la réponse en tant que JSON
            view_data = json.loads(response)
            print(f"Réponse du serveur à la commande 'voir' : {view_data}")
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
        response: str = send_message(self.socket, "connect")
        if not response.isdigit():
            self.close_connection(f"Reponse invalide 'connect': {response}")
        print(f"Réponse du serveur à la commande 'connect' : {response}")


    def broadcast(self, message):
        response = send_message(self.socket, f"broadcast {message}")
        if response != "ok":
            self.close_connection(f"Reponse invalide 'broadcast' : {response}")
        print(f"Réponse du serveur à la commande 'broadcast' : {response}")


    def fork(self):
        response: str = send_message(self.socket, "fork")
        if response.startswith("ok"):
            print(f"Réponse du serveur à la commande 'fork' : {response}")
            return 0
        elif response.startswith("ko"):
            print(f"Réponse du serveur à la commande 'fork' : {response}")
            return 1
        self.close_connection(f"Reponse invalide 'fork': {response}")
            
    
    def incantation(self):
        response: str = send_message(self.socket, "incantation")
        if response.startswith("ok"):
            print(f"Réponse du serveur à la commande 'incantation' : {response}")
            print("Level Up")
            self.level += 1
            return 0
        elif response.startswith("ko"):
            print(f"Réponse du serveur à la commande 'incantation' : {response}")
            return 1
        self.close_connection(f"Reponse invalide 'incantation': {response}")

    def prend(self, ressource):
        response = send_message(self.socket, f"prend {ressource}")
        if response.startswith("ok"):
            print(f"Réponse du serveur à la commande 'prend' : {response}")
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
        response = send_message(self.socket, f"pose {ressource}")
        if response.startswith("ok"):
            print(f"Réponse du serveur à la commande 'pose' : {response}")
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
            
    def has_enough_food(self):
        """Vérifie si le joueur a assez de nourriture."""
        return self.inventory.get("Food", 0) >= 200

player = Player("localhost", 4228, "bobby")  
