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
        self.members: list = []
        self.requests: list = []
        self.ressources: dict = {}
        self.leader: int = 0
        self.coords  = None
        self.level: int = self.player.level
        self.inventory = self.player.inventory
        
    
    def is_grouped(self) -> bool:
        return self.state
        
    def create_group(self):
        self.leader = self.player.id
        self.members.append(self.player.id)
    
    def join_group(self, player):
        self.members.append(player.id)
        
    def leave_group(self, player):
        self.members.remove(player.id)
    
    def send_request(self, player):
        pass
    
    def accept_request(self, player):
        pass
    
    def refuse_request(self, player):
        pass
        
    def missing_ressources(self) -> dict:
        """Détermine la prochaine ressource manquante pour le level up."""
        next_level = self.player.level + 1
        required_ressources = {}
        
        for ressource, quantity in self.levels.get(next_level, {}).items():
            if ressource == "Player":
                continue
            required_ressources[ressource] = max(0, quantity - self.player.inventory.get(ressource, 0))
            if required_ressources[ressource] == 0:
                del required_ressources[ressource]
        if required_ressources:
            return required_ressources
        return None