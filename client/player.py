import socket
import json

connexion_error = "Erreur : la connexion au serveur n'est pas établie."

# def send_message(sock, message):
#     """Envoie un message au serveur via le socket donné et retourne la réponse."""
#     try:
#         # Envoie le message au serveur
#         sock.sendall((message + "\n").encode('utf-8'))
#         # Lire la réponse du serveur
#         response = []
#         while True:
#             part = sock.recv(1024).decode('utf-8')
#             if not part:
#                 break
#             response.append(part)
#         # Combine les parties reçues en une seule chaîne
#         full_response = ''.join(response).strip()
#         return full_response
#     except socket.error as e:
#         return f"Erreur lors de l'envoi du message : {e}"

def send_message(sock, message):
    """Envoie un message au serveur via le socket donné et retourne la réponse."""
    if sock is None:
        print(connexion_error)
        return None
    try:
        # Envoie le message au serveur
        sock.sendall(message.encode('utf-8'))
        
        # Reçoit la réponse du serveur en une seule fois
        response = sock.recv(1024).decode('utf-8').strip()
        response_list = response.split('\n')
        if "You died" in response_list:
            print(response)
            print("Player is dead")
            return None
        return response
        
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
        self.map_coordinates = (0, 0)
        self.map_size = (0, 0)
        self.team_name = team_name
        self.connect_to_server()
        print("Connexion etablie")
        self.check_inventory()
        self.routine()
        
    def check_inventory(self):
        """Demande l'inventaire au serveur et le stocke sous forme de dictionnaire."""
        if self.socket is not None:
            # Envoyer la commande pour demander l'inventaire
            response = send_message(self.socket, "inventaire")
            
            try:
                # Convertir la réponse JSON en dictionnaire
                inventory_data = json.loads(response)
                self.inventory = inventory_data
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
        print(f"Coordonnées de la carte : {self.map_coordinates}")
        print(f"Inventaire: {self.inventory}")
        print("------------------------------\n")
        
    def routine(self):
        while self.socket:
            self.voir()
            self.check_inventory()
            self.droite()
            self.gauche()
            self.avance()
            self.voir()
            self.connect()
            self.broadcast()

    def droite(self):
        response = send_message(self.socket, "droite")
        if response != "ok":
            self.close_connection("Reponse invalide 'droite'")
        print(f"Réponse du serveur à la commande 'droite' : {response}")

    def gauche(self):
        response = send_message(self.socket, "gauche")
        if response != "ok":
            self.close_connection("Reponse invalide 'gauche'")
        print(f"Réponse du serveur à la commande 'gauche' : {response}")

    def avance(self):
        response = send_message(self.socket, "avance")
        if response != "ok":
            self.close_connection("Reponse invalide 'avance'")
        print(f"Réponse du serveur à la commande 'avance' : {response}")


    def voir(self):
        response = send_message(self.socket, "voir")
        
        if response is None:
            self.close_connection("Reponse invalide 'voir'")
            return

        try:
            # Tenter de charger la réponse en tant que JSON
            view_data = json.loads(response)
            self.view = view_data
            print(f"Réponse du serveur à la commande 'voir' : {json.dumps(self.view)}")
        except json.JSONDecodeError:
            # Si la réponse n'est pas un JSON valide, fermer la connexion
            print("Erreur : La réponse du serveur n'est pas en format JSON.")
            self.close_connection("Reponse invalide 'droite'")

    def connect(self):
        response: str = send_message(self.socket, "connect")
        if not response.isdigit():
            self.close_connection("Reponse invalide 'connect'")
        print(f"Réponse du serveur à la commande 'connect' : {response}")

    def broadcast(self):
        response = send_message(self.socket, "broadcast coucou")
        if response != "ok":
            self.close_connection("Reponse invalide 'broadcast'")
        print(f"Réponse du serveur à la commande 'broadcast' : {response}")



player = Player("localhost", 4227, "billy")  
