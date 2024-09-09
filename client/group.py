import random

class Team:
    def __init__(self, etat: str, level:int, name: str):
        self.name: str = name
        self.level: int = level
        self.etat: str = etat
    
    def change_state(self, etat: str):
        self.etat = etat


class Group:
    
    levels = {
        2: {"Player": 1, "Linemate": 1},
        3: {"Player": 2, "Linemate": 1, "Deraumere": 1, "Sibur": 1},
        4: {"Player": 2, "Linemate": 2, "Sibur": 1, "Phiras": 2},
        5: {"Player": 4, "Linemate": 1, "Deraumere": 1, "Sibur": 2, "Phiras": 1},
        6: {"Player": 4, "Linemate": 1, "Deraumere": 2, "Sibur": 1, "Mendiane": 3},
        7: {"Player": 6, "Linemate": 1, "Deraumere": 2, "Sibur": 3, "Phiras": 1},
        8: {"Player": 6, "Linemate": 2, "Deraumere": 2, "Sibur": 2, "Mendiane": 2, "Phiras": 2, "Thystame": 1},
    }
    
    def __init__(self, player):
        self.player = player
        
        self.state: bool = False
        self.team_name: str = self.player.team_name
        self.members: list = []
        self.requests: list = []
        self.ressources: dict = {}
        self.id: int = 0
        self.coords  = None
        self.level: int = self.player.level
        self.needed_ressources = {k: v for k, v in self.levels[self.level + 1].items() if k != "Player"}
        
    def create_group(self):
        self.id = self.player.id
        self.members.append(self.player.id)
        
        # Genere une coordonnes au hasard dans la carte pour le groupe
        self.coords = self.get_random_coords()
        
        message = f"create {self.id} {self.level} {self.team_name}"
        self.player.broadcast(message)
        
        #protege la creation de groupe non necessaire
        print("Memoire")
        for team, team_info in self.player.memory.items():
            team_info: Team
            
            if team_info.etat == "recrute" and team_info.level == self.level:
                self.player.broadcast(f"stop {self.id}")
                return 1
        
        self.recrute()
        return 0
        
    def join_group(self, team_id:int, coords:tuple):
        self.id = team_id
        self.coords = coords
        self.add_player(self.player.id)
        self.add_player(self.id)
        
    def get_random_coords(self):
        return (random.randint(0, self.player.map_size[0] - 1), random.randint(0, self.player.map_size[1] - 1))
        
    def enougth_players(self):
        return len(self.members) == self.levels[self.level + 1]["Player"]

    def recrute(self):
        message = f"recrute {self.id} {self.level} {self.team_name}"
        self.player.broadcast(message)
        
    def add_player(self, player_id):
        if player_id in self.members:
            return
        self.members.append(player_id)
    
    def stop(self):
        self.player.broadcast(f"stop {self.id}")
        self.player.group = None
        
    def start(self):
        members = " ".join(str(member) for member in self.members)
        self.player.broadcast(f"start {members}")
        
    
        
    def player_info(self, player_id:int, linemate:int, deraumere:int, sibur:int, mendiane:int, phiras:int, thystame:int):
        self.ressources[player_id] = {
            "Linemate": linemate,
            "Deraumere": deraumere,
            "Sibur": sibur,
            "Mendiane": mendiane,
            "Phiras": phiras,
            "Thystame": thystame,
        }
        
    def enougth_ressources(self):
        for ressource, quantity in self.needed_ressources.items():
            if sum(player_info[ressource] for player_info in self.ressources.values()) < quantity:
                return False
        return True
    
    def missing_ressources(self):
        """Détermine la prochaine ressource manquante pour le level up. Renvoie un dictionnaire avec la ressource et le nombre manquant"""
        missing = {}
        for ressource, quantity in self.needed_ressources.items():
            if sum(player_info[ressource] for player_info in self.ressources.values()) < quantity:
                missing[ressource] = quantity - sum(player_info[ressource] for player_info in self.ressources.values())
        if not missing:
            return None
        return missing