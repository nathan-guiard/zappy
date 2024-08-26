import socket

def send_message(sock, message):
    """Envoie un message au serveur via le socket donné et retourne la réponse."""
    try:
        # Envoie le message au serveur
        sock.sendall(message.encode('utf-8'))
        
        # Lire la réponse du serveur
        response = []
        while True:
            part = sock.recv(1024).decode('utf-8')
            if not part:
                break
            response.append(part)
        
        # Combine les parties reçues en une seule chaîne
        full_response = ''.join(response).strip()
        return full_response
        
    except socket.error as e:
        return f"Erreur lors de l'envoi du message : {e}"




class Player:
    def __init__(self, hostname, port, team_name):
        self.hostname = hostname
        self.port = port
        self.socket = None
        self.timeout = 5
        self.num_players = 0
        self.map_coordinates = (0, 0)
        self.team_name = team_name
        self.connect_to_server()
        if self.socket:
            print("Connexion etablie")
            self.display_info()
            self.routine()
        

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
                    print(f"Erreur : L'équipe '{self.team_name}' n'existe pas.")
                    self.close_connection()
                    return
                
                parts = response.split('\n')
                if len(parts) != 2:
                    print("Erreur : format de message du serveur invalide.")
                    self.close_connection()
                    return
                
                # Nombre de joueurs
                try:
                    self.num_players = int(parts[0])
                    print(f"Nombre de joueurs dans l'équipe : {self.num_players}")
                except ValueError:
                    print("Erreur : Le nombre de joueurs reçu n'est pas valide.")
                    self.close_connection()
                    return
                
                # Coordonnées de la carte
                try:
                    self.map_coordinates = tuple(map(int, parts[1].split()))
                    print(f"Coordonnées de la carte reçues : {self.map_coordinates}")
                except ValueError:
                    print("Erreur : Les coordonnées de la carte reçues ne sont pas valides.")
                    self.close_connection()
                    return

            else:
                self.close_connection()
                
        except socket.timeout:
            print(f"Connexion échouée : délai d'attente dépassé ({self.timeout} secondes)")
            self.close_connection()
        
        except socket.error as e:
            print(f"Erreur lors de la connexion au serveur: {e}")
            self.close_connection()


    def close_connection(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Connexion fermée.")
            
    def display_info(self):
        """Affiche les informations du joueur."""
        print("\n--- Informations du Joueur ---")
        print(f"Nom de l'équipe : {self.team_name}")
        print(f"Nombre de joueurs dans l'équipe : {self.num_players}")
        print(f"Coordonnées de la carte : {self.map_coordinates}")
        print("------------------------------\n")
        
    def routine(self):
        """Envoie la commande 'voir' au serveur et affiche la réponse."""
        message = "voir\n"
        if self.socket is not None:
            response = send_message(self.socket, message)
            print(f"Réponse du serveur à la commande 'voir' : {response}")
        else:
            print("Erreur : la connexion au serveur n'est pas établie.")




# Exemple d'utilisation
player = Player("localhost", 4227, "billy")  # Change "localhost" et 4242 avec ton hostname et port
