# from player import Player
import math 

class State:
    levels = {
        2: {"Player": 1, "Linemate": 1},
        3: {"Player": 2, "Linemate": 1, "Deraumere": 1, "Sibur": 1},
        4: {"Player": 2, "Linemate": 2, "Sibur": 1, "Phiras": 2},
        5: {"Player": 4, "Linemate": 1, "Deraumere": 1, "Sibur": 2, "Phiras": 1},
        6: {"Player": 4, "Linemate": 1, "Deraumere": 2, "Sibur": 1, "Mendiane": 3},
        7: {"Player": 6, "Linemate": 1, "Deraumere": 2, "Sibur": 3, "Phiras": 1},
        8: {"Player": 6, "Linemate": 2, "Deraumere": 2, "Sibur": 2, "Mendiane": 2, "Phiras": 2, "Thystame": 1},
    }
    player = None
    target_coords = None
    required_ressources = None
    
    def enter_state(self):
        pass

    def exit_state(self):
        pass

    def update(self):
        return None


class Idle(State):
    def __init__(self, player) -> None:
        self.player = player
        
    def enter_state(self):
        print("Je suis rentré en état IDLE")
    
    def exit_state(self):
        print("Je suis sorti de l'état IDLE")

    def update(self) -> State:
        self.required_ressources = self.missing_ressources()
        self.target_coords = self.choisir_meilleure_case()
        self.player.check_inventory()
        self.player.voir()
        if self.required_ressources is None:
            return Incantation(self.player)
        elif self.player.inventory.get("Food", 0) < 200:
            return Nourrir(self.player)
        elif self.player.coordinates == self.target_coords:
            return Recolte(self.player)
        elif self.target_coords:
            return Deplacement(self.player, self.target_coords)
        return Exploration(self.player)
    
    def missing_ressources(self) -> str:
        """Détermine la prochaine ressource manquante pour le level up."""
        next_level = self.player.level + 1
        required_ressources = {}
        
        for ressource, quantity in self.levels.get(next_level, {}).items():
            if ressource == "Player":
                continue
            required_ressources[ressource] = max(0, quantity - self.player.inventory.get(ressource.lower(), 0))
        if required_ressources:
            return required_ressources
        return None
    
    def choisir_meilleure_case(self):
        """Choisit la meilleure case en fonction des ressources manquantes"""
        best_tile = None
        best_score = -1
        if self.required_ressources is None:
            return None
        for coords, resources in self.player.view.items():
            score = self.evaluate_tile(resources)
            if score > best_score:
                best_score = score
                best_tile = coords
                self.player.focus = resources
        if best_score == 0:
            return None
        return best_tile

    def evaluate_tile(self, resources):
        """Évalue une case en fonction des ressources manquantes et retourne un score."""
        score = 0
        for resource, needed_quantity in self.required_ressources.items():
            if resource.lower() in resources:
                available_quantity = resources[resource.lower()]
                score += min(needed_quantity, available_quantity) * 10  # Pondération par ressource
        return score


class Exploration(State):
    def __init__(self, player):
        self.player = player

    def enter_state(self):
        print(f"Je suis en état Exploration")
    
    def exit_state(self):
        print(f"Sorti de l'état Exploration")
    
    def update(self) -> State:
        if self.player.coordinates == self.target_coords:
            return Idle(self.player)  # Retour à l'état précédent (Recherche ou autre)
        return self  # Reste dans l'état Deplacement jusqu'à atteindre la cible


class Recolte(State):
    def __init__(self, player):
        self.player = player

    def enter_state(self):
        print("Je suis en état RECOLTE")
    
    def exit_state(self):
        self.player.display_info()
        print("Je suis sorti de l'état RECOLTE")

    def update(self) -> State:
        """Essaye de récolter les ressources de la case actuelle"""
        for ressource, quantity in self.player.focus.items():
            for _ in range(quantity):
                if self.player.prend(ressource):
                    return Idle(self.player)
        return self


class Nourrir(State):
    def __init__(self, player):
        self.player = player

    def enter_state(self):
        print("Je suis en état Nourrir")
        self.target_coords = self.choisir_meilleure_case()
    
    def exit_state(self):
        print("Je suis sorti de l'état Nourrir")
    
    def update(self) -> State:
        """Si le joueur a assez de nourriture, retourne à l'état précédent.
        Sinon continue de chercher de la nourriture.
        Et de la recolter si possible."""
        
        if self.player.inventory.get("Food", 0) >= 1000:
            return Idle(self.player)
        
        if self.target_coords is None:
            return Exploration(self.player)
        
        if self.target_coords is not None:
            self.deplacer_vers(self.target_coords)
            if self.player.coordinates == self.target_coords:
                self.player.collect_food()
                self.target_coords = self.choisir_meilleure_case()
        return self
    
    def choisir_meilleure_case(self):
        """Choisit la meilleure case en fonction des ressources manquantes"""
        best_tile = None
        best_score = -1
        for coords, resources in self.player.view.items():
            score = self.evaluate_tile(resources)
            if score > best_score:
                best_score = score
                best_tile = coords
        return best_tile
    
    def evaluate_tile(self, resources):
        """Évalue une case en fonction des ressources manquantes et retourne un score."""
        score = 0
        for resource, quantity in resources.items():
            if resource == "food":
                score += quantity
        return score

class Deplacement(State):
    def __init__(self, player, target_coords):
        self.player = player
        self.target_coords = target_coords

    def enter_state(self):
        print(f"Je suis en état DEPLACEMENT vers {self.target_coords}")
    
    def exit_state(self):
        print(f"J'ai atteint la cible {self.target_coords}, sorti de l'état DEPLACEMENT")
    
    def update(self) -> State:
        if self.player.coordinates == self.target_coords:
            print(f"Joueur arrivé à la destination {self.target_coords}")
            return None  # Retour à l'état précédent (Recherche ou autre)

        self.deplacer_vers(self.target_coords)
        return self  # Reste dans l'état Deplacement jusqu'à atteindre la cible

    def deplacer_vers(self, target_coords):
        """Se déplace vers les coordonnées cibles en prenant en compte la direction actuelle."""
        current_x, current_y = self.player.coordinates
        target_x, target_y = target_coords

        if current_x < target_x:
            self.orienter_vers('E')
        elif current_x > target_x:
            self.orienter_vers('W')
        elif current_y < target_y:
            self.orienter_vers('N')
        elif current_y > target_y:
            self.orienter_vers('S')
        
        # Une fois orienté, avance
        self.player.avance()

    def orienter_vers(self, direction):
        """Oriente le joueur vers la direction désirée avant de se déplacer."""
        while self.player.direction != direction:
            self.player.droite()
        print(f"Joueur orienté vers {direction}")

    

class Incantation(State):
    def __init__(self, player):
        self.player = player

    def enter_state(self):
        print("Je suis en état INCANTATION")
    
    def exit_state(self):
        print("Je suis sorti de l'état INCANTATION")

    def update(self) -> State:
        self.player.incantation()
        # Implémentez la logique de l'incantation ici
        return None
