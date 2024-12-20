import socket, json, argparse, multiprocessing, signal, sys
from states.state import Idle
from states.group import Group, Team
from states.color import color
from time import time
from datetime import datetime
    
connexion_error = "Erreur : la connexion au serveur n'est pas établie."
Direction = ['N', 'E', 'S', 'W']

class Player:
    """Classe principale pour le joueur."""
    
    RESOURCE_SCORES = {
        'Linemate': 10,
        'Deraumere': 8,
        'Sibur': 6,
        'Mendiane': 5,
        'Phiras': 7,
        'Thystame': 9
    }
    
    map_memory = {}
    
    def __init__(self, hostname, port, team_name):
        self.hostname = hostname
        self.port = port
        self.view = {}
        signal.signal(signal.SIGINT, self.handle_signal)
        self.id = multiprocessing.current_process().pid
        self.socket = None
        self.timeout = 10
        self.inventory = {
            "Food": 0,
            "Linemate": 0,
            "Deraumere": 0,
            "Sibur": 0,
            "Mendiane": 0,
            "Phiras": 0,
            "Thystame": 0
        }
        self.available_connexion = 0
        self.coordinates = (0, 0)
        self.direction = Direction[0]
        self.map_size = (0, 0)
        self.team_name = team_name
        self.level = 1
        self.focus_ressources = None
        self.focus_coords = None
        self.communication = []
        self.buffer = ""
        self.have_fork = False
        self.list_processus = []
        self.state = Idle(self)  # Débuter en état Idle
        self.waiting_broadcast = []
        
        self.connect_to_server()
        self.inventaire()
        self.voir()
        # self.display_info()
        
        # La memoire stocks les informations des broadcasts
        self.memory = {}
        self.map_memory = {}
        self.groups = None
        self.state.enter_state()
        self.tik = 0
        self.players = {}
        self.routine()
        
    def connect_to_server(self):
        try:
            # print(f"Tentative de connexion au serveur {self.hostname}:{self.port}...")
            
            # Crée un socket TCP/IP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Définit un timeout pour la connexion
            self.socket.settimeout(self.timeout)
            
            # Tente de se connecter au serveur
            self.socket.connect((self.hostname, self.port))
            # print(f"Connexion établie avec le serveur {self.hostname}:{self.port}")
            
            # Recevoir le message de bienvenue
            welcome_message = self.socket.recv(1024).decode('utf-8')
            # print(f"Message reçu du serveur : {welcome_message}")
            
            if "BIENVENUE" in welcome_message:
                # Envoyer le nom de l'équipe
                self.socket.sendall(f"{self.team_name}\n".encode('utf-8'))
                # print(f"Nom de l'équipe '{self.team_name}' envoyé au serveur.")
                
                 # Recevoir la réponse du serveur après l'envoi du nom d'équipe
                response = self.socket.recv(1024).decode('utf-8').strip()
                if "does not exist" in response:
                    self.close_connection(f"Erreur : L'équipe '{self.team_name}' n'existe pas.")
                    return
                
                if "is full" in response:
                    self.close_connection(f"Erreur : L'équipe '{self.team_name}' est pleine.", silent=True)
                    return
                
                parts = response.split('\n')
                if len(parts) != 2:
                    self.close_connection(f"Erreur : format de message du serveur invalide. {response}")
                    return
                
                # Connexion disponible
                try:
                    self.available_connexion = int(parts[0])
                except ValueError:
                    self.close_connection(f"Erreur : Le nombre de connexion reçu n'est pas valide. {response}")
                    return
                
                if self.available_connexion == 0:
                    self.close_connection("Erreur : Aucune connexion disponible.", code=1, silent=True)
                    return
                
                # Coordonnées de la carte
                try:
                    self.map_size = tuple(map(int, parts[1].split()))
                    # print(f"Coordonnées de la carte reçues : {self.map_size}")
                except ValueError:
                    self.close_connection(f"Erreur : La taille de la carte reçues n'est pas valide. {response}")
                    return

            else:
                self.close_connection("Erreur de connexion")

        except socket.timeout:
            self.close_connection(f"Connexion échouée : délai d'attente dépassé ({self.timeout} secondes)")
        
        except socket.error as e:
            self.close_connection(f"Erreur lors de la connexion au serveur: {e}")
            

    def send_message(self, message, send=True):
        """Envoie un message au serveur via le socket donné et retourne la réponse complète jusqu'à réception du caractère de fin \x04.
        Gère également les messages fragmentés avec un buffer circulaire et journalise chaque communication dans un fichier de log pour chaque joueur."""
        
        if self.socket is None:
            print(connexion_error)
            return None
        
        # Initialisation du buffer s'il n'existe pas encore
        if not hasattr(self, 'buffer'):
            self.buffer = ""

        # Nom du fichier de log pour le joueur
        # log_filename = f"datas/player_{self.id}_log.txt"
        
        try:
            # Envoie le message au serveur et le journalise
            if send:
                self.socket.sendall(message.encode('utf-8'))
                # Journaliser l'envoi du message
                # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # with open(log_filename, 'a') as log_file:
                    # log_file.write(f"[{current_time}] - SENT: {message}\n")
            
            response_list = []
            
            # Réception des données en plusieurs parties
            while True:
                part: str = self.socket.recv(1024).decode('utf-8')
                if not part:
                    # with open(log_filename, 'a') as log_file:
                    #     log_file.write(f"[{current_time}] - Buffer: {self.buffer}\n")
                
                    response_list = list(filter(None, self.buffer.strip().replace('\x04', '').split('\n')))
                    # print(response_list)
                    for received in response_list:
                        if received.startswith("You died") or received.startswith("End of game") or received.startswith("Disconnected"):
                            print(f"{self.id}: {received}")
                            return None
                    
                    # Connexion perdue ou fin de transmission inattendue
                    print(f"{self.id}: Connexion perdue ou transmission incomplète")
                    # print(f"x04 in self buffer : {'\x04' in self.buffer}")
                    return None
                
                # Ajouter la nouvelle partie au buffer
                self.buffer += part
            

                # Tant qu'on trouve un séparateur '\x04' dans le buffer, on extrait un message complet
                while '\x04' in self.buffer:
                    # Découpe le buffer en utilisant '\x04' comme séparateur
                    message_complete, self.buffer = self.buffer.split('\x04', 1)
                    # if self.buffer:
                        # print(f"{self.id} : Message fragmenté reçu : {message_complete}, buffer : {self.buffer}")

                    # Gérer le message complet (sans '\x04')
                    response_list = list(filter(None, message_complete.strip().split('\n')))

                    # Journaliser la réponse du serveur
                    # with open(log_filename, 'a') as log_file:
                    #     log_file.write(f"[{current_time}] - RECEIVED: {message_complete}\n")
                    #     log_file.write(f"[{current_time}] - Buffer: {self.buffer}\n")


                    # Vérification des réponses critiques
                    for received in response_list:
                        if received.startswith("You died") or received.startswith("End of game"):
                            print(f"{self.id}: {received}")
                            return None
                    
                    # Sélection de la réponse finale à renvoyer
                    final_response = None
                    for response in response_list:
                        if response.startswith("broadcast"):
                            self.communication.append(response.split(' ')[1:])
                        else:
                            final_response = response

                    return final_response

        except socket.error as e:
            # if e.errno == 104:
            #     return None
            # print(f"Erreur lors de l'envoi du message : {e}")
            return None


    def close_connection(self, error_message: str = None, code: int = 0, silent: bool = False):
        if error_message and not silent:
            # print(error_message)
            self.socket.close()
            self.socket = None
            # if not silent:
            #     print(f"{self.id} : Connexion fermée.")
        self.close_all_processes()
        exit(code)
    
    # Gestionnaire de signaux
    def handle_signal(self, signum, frame):
        print(f"Signal de fermeture reçu {self.id}. Fermeture des sous-processus...")
        self.close_all_processes()
        exit(0)

    # Méthode pour fermer les sous-processus proprement
    def close_all_processes(self):
        """Ferme tous les sous-processus proprement."""
        for process in self.list_processus:
            if process.is_alive():
                process.join()
                # print(f"Child process {process.pid} terminated.")
        self.list_processus = []
        
        
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
            # print(f"Inventaire mis à jour : {self.inventory}")
        except json.JSONDecodeError:
            self.close_connection(f"{self.id} : Erreur : Impossible de décoder la réponse JSON du serveur.")
        except TypeError:
            self.close_connection(f"{self.id} : Erreur : Type de données invalide pour l'inventaire.:", response)

    def display_info(self):
        """Affiche les informations du joueur."""
        print("\n--- Informations du Joueur ---")
        print(f"ID du joueur : {self.id}")
        print(f"Nom de l'équipe : {self.team_name}")
        print(f"Level du joueur : {self.level}")
        print(f"Coordonnées de la carte : {self.coordinates}")
        print(f"Direction: {self.direction}")
        print(f"Inventaire: {self.inventory}")
        # print(f"Memoire: {self.view}")
        print("------------------------------\n")
        
    def routine(self):
        """Boucle principale pour gérer les actions du joueur."""
        while self.socket:
            self.ticker()
            self.update()
            self.death_detection()
            
    def death_detection(self):
        current_time = time()
        inactivity_threshold = 30 # Seuil d'inactivité en secondes
        inactive_players = []

        # Parcourir tous les joueurs connus et vérifier leur dernier timestamp
        for player_id, last_alive_time in self.players.items():
            if player_id == self.id:
                continue
            # Si un joueur n'a pas donné signe de vie depuis un certain temps (par exemple, 60 secondes)
            if current_time - last_alive_time > inactivity_threshold:
                # print(f"Player {player_id} is considered dead (inactive for too long).")
                inactive_players.append(player_id)
                self.handle_death(player_id)  # Appeler une fonction pour gérer la mort du joueur

        # Supprimer les joueurs inactifs de la liste des joueurs vivants
        for player_id in inactive_players:
            del self.players[player_id]

    def handle_death(self, player_id):
        # Supprime un joueur du groupe s'il est dans un groupe
        if self.groups and player_id in self.groups.members:
            # print(f"Removing player {player_id} from group due to inactivity.")
            self.groups.remove_player(player_id)


    def ticker(self):
        """Appelée à chaque cycle de jeu pour gérer les actions du joueur."""
        alive = 50
        
        self.tik += 1
        if self.tik % alive == 0:
            message = f"alive {self.id}"
            self.waiting_broadcast.append(f"{message}")

    def droite(self):
        response = self.send_message("droite")
        if response is None:
            self.close_connection()
        if response != "ok":
            self.close_connection(f"{self.id} : Reponse invalide 'droite': {response}")
        current_index = Direction.index(self.direction)
        self.direction = Direction[(current_index + 1) % len(Direction)]
        # print(f"Réponse du serveur à la commande 'droite' : {response}")

    def gauche(self):
        response = self.send_message("gauche")
        if response is None:
            self.close_connection()
        if response != "ok":
            self.close_connection(f"{self.id} : Reponse invalide 'gauche': {response}")
        current_index = Direction.index(self.direction)
        self.direction = Direction[(current_index - 1) % len(Direction)]
        # print(f"Réponse du serveur à la commande 'gauche' : {response}")


    def avance(self):
        response = self.send_message("avance")
        if response is None:
            self.close_connection()
        if response != "ok":
            self.close_connection(f"{self.id} : Reponse invalide 'avance': {response}")
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

        try:
            # Convertir la réponse JSON en dictionnaire
            view_data = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            self.close_connection(f"{self.id} : Réponse invalide 'voir' : {response}")
            return

        # Update la position du joueur
        player_tile = view_data[0]
        self.coordinates = (player_tile['p']['x'], player_tile['p']['y'])

        # Affichage de la vue
        # print(f"Vue du joueur : {view_data}")

        for tile in view_data:
            tile_coords = (tile['p']['x'], tile['p']['y'])
            new_resources = tile['c'][0] if tile['c'] else {}
            old_resources = self.view.get(tile_coords, {})
            self.view[tile_coords] = new_resources

            # Mettre à jour la mémoire avec les nouvelles ressources trouvées
            self.update_memory(tile_coords, old_resources, new_resources)

    def update_memory(self, tile_coords, old_resources, new_resources):
        """
        Met à jour le score dans la mémoire en fonction des ressources trouvées.
        Ajoute uniquement le score pour les nouvelles ressources ou les quantités augmentées.
        """
        if tile_coords not in self.map_memory:
            self.map_memory[tile_coords] = 0
        for resource, count in new_resources.items():
            if resource not in self.RESOURCE_SCORES:
                continue  # Ignore les ressources inconnues
            # print(f"Ressource {resource} : {count}")
            old_count = old_resources.get(resource, 0)
            if count > old_count:
                increment = self.RESOURCE_SCORES[resource] * (count - old_count)
                if tile_coords in self.map_memory:
                    self.map_memory[tile_coords] += increment
                else:
                    self.map_memory[tile_coords] = increment
                # print(f"Ajout de {increment} points à la zone {tile_coords} pour {resource}.")
        # name = f"py/datas/{self.id}.json"
        # map_memory_str_keys = {str(key): value for key, value in self.map_memory.items()}
        # with open(name, "w") as file:
        #     json.dump(map_memory_str_keys, file)

    def connect(self):
        response = self.send_message("connect")
        if response is None:
            self.close_connection()
        if not response.isdigit():
            self.close_connection(f"{self.id} : Reponse invalide 'connect': {response}")
        # print(f"Réponse du serveur à la commande 'connect' : {response}")
        return int(response)

    def broadcast(self, message=None):
        if message is None and not self.waiting_broadcast:
            return
        if message is not None:
            self.waiting_broadcast.append(message)
        message = "\x03".join(self.waiting_broadcast)
        # print(f"Broadcasting message: {message}")
        response = self.send_message(f"broadcast {message}")
        if response is None:
            self.close_connection()
        if response != "ok":
            self.close_connection(f"{self.id} : Reponse invalide 'broadcast' : {response}")
        # print(f"Réponse du serveur à la commande 'broadcast' : {response}")
        self.waiting_broadcast = []
        self.communicate()

    def fork_manager(self):
        """Suite a la commande fork, si une connexion est possible, visible avec la command connect, alors on peut rajouter un nouveau player"""
        connect = self.connect()
        if connect == 0:
            return
        # Creation d'un nouveau multiprocessus pour le nouveau joueur
        process = multiprocessing.Process(target=Player, args=(self.hostname, self.port, self.team_name))
        process.start()
        process.join(timeout=1)
        if not process.is_alive():
            # print(f"Connect: {connect}, {color('Ko', 'red_bg')}")
            # print(color("Process est pas cree", "red_bg"))
            return
        # print(f"Connect: {connect}, {color('Ok', 'green_bg')}")
        self.list_processus.append(process)
        self.have_fork = False
    
    def fork(self):
        # random 10% de chance de fork
        # if random.randint(0, 2) != 0:
        #     return 1
        response = self.send_message("fork")
        if response is None:
            self.close_connection()
        if response.startswith("ok"):
            self.have_fork = True
            # print(f"Fork: {self.team_name}, {color('Ok', 'green_bg')}")
            # print(f"Réponse du serveur à la commande 'fork' : {response}")
            return 0
        elif response.startswith("ko"):
            pass
            # print(f"Réponse du serveur à la commande 'fork' : {response}")
            # print(f"Fork: {self.team_name}, {color('Ko', 'red_bg')}")
            return 1
        self.close_connection(f"{self.id} : Reponse invalide 'fork': {response}")
    
    def incantation(self):
        # Ralonger le socket.timeout
        self.socket.settimeout(self.timeout * 10)
        response = self.send_message("incantation")
        # print(f"Réponse du serveur à la commande 'incantation' : {response}")
        self.socket.settimeout(self.timeout)
        if response is None:
            self.close_connection()
        if response.startswith("ok"):
            # print(f"Réponse du serveur à la commande 'incantation' : {response}")
            # print("Level Up")
            self.level += 1
            if self.level == 8:
                print(f"{self.id}: {color('Niveau 8', 'green_bg')}")
                self.close_connection()
            return 0
        elif response.startswith("ko"):
            # print(f"Réponse du serveur à la commande 'incantation' : {response}")
            return 1
        self.close_connection(f"{self.id} : Reponse invalide 'incantation': {response}")

    def prend(self, ressource):
        response = self.send_message(f"prend {ressource}")
        if response is None:
            self.close_connection()
            
        ressource = ressource.capitalize()
            
        if response.startswith("ok"):
            # print(f"Réponse du serveur à la commande 'prend' : {response}")
            if ressource == "Food":
                self.inventory[ressource] += 126
            else:
                self.inventory[ressource] += 1

            if ressource in self.view[self.coordinates]:
                self.view[self.coordinates][ressource] -= 1
            else:
                self.view[self.coordinates][ressource] = 0
            return 0
        elif response.startswith("ko"):
            self.voir()
            return 1
        else: 
            self.close_connection(f"{self.id} : Reponse invalide 'prend' : {response}")

    def pose(self, ressource):
        response = self.send_message(f"pose {ressource}")
        if response is None:
            self.close_connection()
        
        if response.startswith("ok"):
            self.inventory[ressource] -= 1
            # print(f"Réponse du serveur à la commande 'pose' : {response}")
        elif response.startswith("ko"):
            self.voir()
        else: 
            self.close_connection(f"{self.id} : Reponse invalide 'pose' : {response}")
    
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
        for messages in self.communication:
            # direction: player_information player_id lvl x y linemate deraumere sibur mendiane phiras thystame
            # Parsing des messages de types : f"Player_information {self.player.id} {self.player.level} {self.player.coordinates} {self.player.inventory}"
            # direction = int(messages[0][:-1])
            messages = " ".join(messages[1:]).split('\x03')
            # print(messages)
            for message in messages:
                message = message.split(' ')
                # print(f"Gestion du message {message}")
                message_type = message[0]
                # print(f"Message type: {message_type}")
                
                if message_type == "create":
                    self.handle_create(message[1:])
                elif message_type == "recrute":
                    self.handle_recrute(message[1:])
                elif message_type == "interested":
                    self.handle_interested(message[1:])
                elif message_type == "accept":
                    self.handle_accept(message[1:])
                elif message_type == "kick":
                    self.handle_kick(message[1:])
                elif message_type == "start":
                    self.handle_start(message[1:])
                elif message_type == "stop":
                    self.handle_stop(message[1:])
                elif message_type == "info":
                    self.handle_info(message[1:])
                elif message_type == "alive":
                    self.handle_alive(message[1:])
                
        self.communication = []
        self.broadcast()
        
    def handle_kick(self, message):
        # kick {team_id} {player_id}
        try:
            team_id = int(message[0])
            player_id = int(message[1])
        except Exception as e:
            print(f"{self.id} : Erreur lors de la reception du message de kick: {e} '{message}'")
            return
        
        if self.groups is None:
            return
        
        if self.groups.id == team_id:
            if player_id in self.id:
                self.groups = None
                print(f"Je me suis fait kicker du groupe {team_id}")
            else:
                print(f"{player_id} a ete kick du groupe {team_id}")
                self.groups.remove_player(player_id)
            return
    
    def handle_alive(self, message):
        # alive {self.id}
        try:
            player_id = int(message[0])
        except Exception as e:
            print(f"{self.id} : Erreur lors de la reception du message d'alive: {e} '{message}'")
            return
        
        self.players[player_id] = time()
        
    def handle_create(self, message):
        # create {self.id} {self.level} {self.team_name}
        try:
            team_id = int(message[0])
            team_level = int(message[1])
            team_name = message[2]
        except Exception as e:
            print(f"{self.id} : Erreur lors de la reception du message de creation: {e} '{message}'")
            return
        
        self.players[team_id] = time()
        
        # if team_level != self.level: # nous ajouterons un filtre sur le nom de 'team_name' plus tard
            # return
        
        self.memory[team_id] = Team("create", team_level, team_name)
    
    def handle_recrute(self, message):
        # recrute {self.id} {self.level} {self.team_name}
        try:
            team_id = int(message[0])
            team_level = int(message[1])
            team_name = message[2]
            
        except Exception as e:
            print(f"{self.id} : Erreur lors de la reception du message de recrute: {e} '{message}'")
            return
        
        self.players[team_id] = time()
        
        if team_id not in self.memory:
            self.memory[team_id] = Team("recrute", team_level, team_name)
        else:
            self.memory[team_id].change_state("recrute")
    
    def handle_interested(self, message):
        # interested {self.id_team} {self.id_player} 
        try:
            team_id = int(message[0])
            player_id = int(message[1])
        except Exception as e:
            print(f"{self.id} : Erreur lors de la reception du message d'interet: {e} '{message}'")
            return
        
        self.players[player_id] = time()
        
        # Si je n'ai pas de groupe
        if self.groups is None:
            return
        
        # Si je ne suis pas le leader
        if self.id != team_id:
            return
        
        # Si on manque de membres
        if not self.groups.enougth_players():
            # On accepte
            self.groups.add_player(player_id)
            self.accept(team_id, player_id)
            if self.groups.enougth_players():
               self.groups.start() 
        
        
    def handle_accept(self, message):
        # accept {team_id} {player_id} {self.groups.coords[0]},{self.groups.coords[1]} {members}
        try:
            team_id = int(message[0])
            player_id = int(message[1])
            coords = tuple(map(int, message[2].split(',')))
            members = list(map(int, message[3:]))
            
        except Exception as e:
            print(f"{self.id} : Erreur lors de la reception du message d'acceptation: {e} '{message}'")
            return
        
        self.players[player_id] = time()
        
        # print(f"Grouper : {self.groups}")
        if self.groups:
            return
        
        if self.id != player_id:
            return
        # print(f"Je suis accepte dans le groupe {team_id}")
        if team_id not in self.memory:
            return
        
        self.groups = Group(self)
        self.groups.join_group(team_id, coords)
        
        for member in members:
            self.groups.add_player(member)
        
        
        
    def handle_start(self, message):
        # start {team_id} {id} {id} {id}...
        try:
            team_id = int(message[0])
            players = list(map(int, message[0:]))
        except Exception as e:
            print(f"{self.id} : Erreur lors de la reception du message de debut: {e} '{message}'")
            return
        
        self.players[team_id] = time()
        
        if team_id in self.memory:
            del self.memory[team_id]
            
        if self.groups is None:
            return
        
        if self.id in players:
            for player in players:
                if player != self.id:
                    self.groups.add_player(player)
                    
    def handle_stop(self, message):
        # stop {team_id}
        try:
            team_id = int(message[0])
        except Exception as e:
            print(f"{self.id} : Erreur lors de la reception du message de fin: {e} '{message}'")
            return
        
        self.players[team_id] = time()
        
        if team_id in self.memory:
            del self.memory[team_id]
        
        if self.groups:
            if self.groups.id == team_id:
                # print(f"Reception d'un stop du groupe {self.groups.id}")
                self.groups = None
                # print(f"Groupe detruit {self.groups}")
                
    def handle_info(self, message):
        # info {team_id} {id} {linemate} {deraumere} {sibur} {mendiane} {phiras} {thystame}
        try:
            team_id = int(message[0])
            player_id = int(message[1])
            linemate = int(message[2])
            deraumere = int(message[3])
            sibur = int(message[4])
            mendiane = int(message[5])
            phiras = int(message[6])
            thystame = int(message[7])
        except Exception as e:
            print(f"{self.id} : Erreur lors de la reception du message d'information: {e} '{message}'")
            return
        
        self.players[player_id] = time()
        
        if self.groups is None:
            return
        
        if self.groups.id == team_id:
            self.groups.player_info(player_id, linemate, deraumere, sibur, mendiane, phiras, thystame)
        
    def accept(self, team_id: int, player_id: int):
        members = " ".join(str(member) for member in self.groups.members)
        message = f"accept {team_id} {player_id} {self.groups.coords[0]},{self.groups.coords[1]} {members}"
        self.waiting_broadcast.append(message)
        
    def refuse(self, team_id: int, player_id: int):
        message = f"refuse {team_id} {player_id}"
        self.waiting_broadcast.append(message)
    
    def interested(self, team_id: int):
        message = f"interested {team_id} {self.id}"
        self.broadcast(message)
    
    def info(self):
        message = f"info {self.groups.id} {self.id} {self.inventory['Linemate']} {self.inventory['Deraumere']} {self.inventory['Sibur']} {self.inventory['Mendiane']} {self.inventory['Phiras']} {self.inventory['Thystame']}"
        self.groups.player_info(self.id, self.inventory['Linemate'], self.inventory['Deraumere'], self.inventory['Sibur'], self.inventory['Mendiane'], self.inventory['Phiras'], self.inventory['Thystame'])
        self.broadcast(message)
        
    def stop(self):
        message = f"stop {self.groups.id}"
        # print(f"Stop : Arret du groupe {self.groups.id}")
        self.groups = None
        # print(f"Stop : Groupe detruit {self.groups}")
        self.broadcast(message)
    
    def create_group(self):
        self.groups = Group(self)
        if self.groups.create_group():
            # print("Annulation de la creation de groupe")
            self.groups = None
            return
        # print("Groupe cree")
        
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

    # Vérification des valeurs des arguments
    if not 1024 <= args.port <= 65535:
        print("Erreur: Le numéro de port doit être compris entre 1024 et 65535.\n")
        return 1
    
    player = Player(args.hostname, args.port, args.team)

