# from player import Player
import math 
import random
from states.color import color

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
    
    def calculate_toric_distance(self, current, target, dimension_size):
        """Calcule la distance torique la plus courte entre deux points."""
        direct_distance = target - current
        if direct_distance > dimension_size // 2:
            return direct_distance - dimension_size
        elif direct_distance < -dimension_size // 2:
            return direct_distance + dimension_size
        return direct_distance
    
    def distance_toric(self, destination):
        """Calcul la distance torique entre deux points."""
        x1, y1 = self.player.coordinates
        x2, y2 = destination
        dx = self.calculate_toric_distance(x1, x2, self.player.map_size[0])
        dy = self.calculate_toric_distance(y1, y2, self.player.map_size[1])
        return abs(dx) + abs(dy)


class Idle(State):
    def __init__(self, player) -> None:
        self.player = player
        
    def enter_state(self):
        print(f"Je suis rentré en état {color('IDLE', 'green')}")
    
    def exit_state(self):
        print(f"Je suis sorti de l'état {color('IDLE', 'green')}")

    def update(self) -> State:
        self.required_ressources = self.missing_ressources()
        if self.player.focus_coords is None:
            self.target_coords = self.choisir_meilleure_case()
            self.player.focus_coords = self.target_coords
            
        self.player.check_inventory()
        
        if self.player.inventory.get("Food", 0) < 200 and self.player.focus_ressources is None:
            return Nourrir(self.player)
        elif self.required_ressources is None and self.player.focus_coords is None:
            return Incantation(self.player)
        elif self.player.focus_coords and self.player.focus_coords != self.player.coordinates:
            return Deplacement(self.player, self.player.focus_coords)
        elif self.player.coordinates == self.target_coords:
            return Recolte(self.player)
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
                self.player.focus_ressources = resources
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
    def __init__(self, player, grid_size=5):
        self.player = player
        self.grid_size = grid_size
        self.grids = self.generate_grids()
        self.current_grid = None
        self.middle_coords = None

    def enter_state(self):
        print(f"Je suis en état {color('Exploration', 'blue')}")
        self.current_grid = self.find_next_grid()
        if self.current_grid:
            self.middle_coords = self.get_middle_of_grid(self.current_grid)
        else:
            print("Toutes les grilles sont explorées.")

    def exit_state(self):
        print(f"Sorti de l'état {color('Exploration', 'blue')}")
    
    def update(self) -> State:
        """Update pour le cycle d'exploration."""
        if self.player.coordinates == self.middle_coords and self.player.focus_coords:
            self.explore_grid_center()
            self.player.focus_coords = None
            return Idle(self.player)
        return Deplacement(self.player, self.middle_coords)

    def generate_grids(self):
        """Génère une liste des centres des grilles sur la carte."""
        grids = []
        map_width, map_height = self.player.map_size
        
        for x in range(0, map_width, self.grid_size):
            for y in range(0, map_height, self.grid_size):
                grids.append((x, y))
        
        return grids

    def find_next_grid(self):
        """Trouve la prochaine grille non explorée."""
        random.shuffle(self.grids)
        for grid_start in self.grids:
            if not self.is_grid_explored(grid_start):
                return grid_start
        return None

    def is_grid_explored(self, grid_start):
        """Vérifie si une grille entière est explorée."""
        x_start, y_start = grid_start
        for x in range(x_start, x_start + self.grid_size):
            for y in range(y_start, y_start + self.grid_size):
                if (x, y) not in self.player.view:
                    return False  # Il reste des cases non explorées
        return True  # Toute la grille est explorée

    def get_middle_of_grid(self, grid_start):
        """Calcule les coordonnées du milieu de la grille et vérifie si elles sont explorées."""
        x_start, y_start = grid_start
        middle_coords = (x_start + self.grid_size // 2, y_start + self.grid_size // 2)
        if middle_coords not in self.player.view:
            return middle_coords
        # Si le milieu est déjà exploré, trouve une autre case non explorée
        for x in range(x_start, x_start + self.grid_size):
            for y in range(y_start, y_start + self.grid_size):
                if (x, y) not in self.player.view:
                    return (x, y)
        return None

    def move_to(self, target_coords):
        """Déplace le joueur vers les coordonnées cibles."""
        if target_coords != self.player.coordinates:
            Deplacement(self.player, target_coords).enter_state()

    def explore_grid_center(self):
        """Explore le centre de la grille en tournant sur soi-même."""
        self.player.voir()  # Voir en direction initiale
        for _ in range(3):
            self.player.droite()  # Tourne à droite
            self.player.voir()  # Voir dans la nouvelle direction




class Recolte(State):
    def __init__(self, player):
        self.player = player

    def enter_state(self):
        print(f"Je suis en état {color('RECOLTE', 'lightgreen')}")
    
    def exit_state(self):
        self.player.display_info()
        print(f"Je suis sorti de l'état {color('RECOLTE', 'lightgreen')}")

    def update(self) -> State:
        """Essaye de récolter les ressources de la case actuelle"""
        for ressource, quantity in self.player.focus_ressources.items():
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
        self.player.focus_coords = target_coords
        self.map_width, self.map_height = player.map_size

    def enter_state(self):
        print(f"Je suis en état {color('DEPLACEMENT', 'pink')} vers {self.player.focus_coords}")

    def exit_state(self):
        print(f"J'ai atteint la cible {self.player.focus_coords}, sorti de l'état {color('DEPLACEMENT', 'pink')}")
    
    def update(self) -> State:
        if self.player.coordinates == self.player.focus_coords:
            print(f"Joueur arrivé à la destination {self.player.focus_coords}")
            return Idle(self.player)  # Retour à l'état précédent ou un autre état
        
        self.move_to_target()
        return None  # Reste dans l'état Deplacement jusqu'à atteindre la cible

    def move_to_target(self):
        """Se déplace vers les coordonnées cibles en prenant en compte la carte torique."""
        current_x, current_y = self.player.coordinates
        target_x, target_y = self.player.focus_coords
        print(f"Joueur en ({current_x}, {current_y}), cible en ({target_x}, {target_y})")
         
        # Calcul du déplacement optimal en tenant compte de la carte torique
        delta_x = self.calculate_toric_distance(current_x, target_x, self.map_width)
        delta_y = self.calculate_toric_distance(current_y, target_y, self.map_height)
        print(f"Déplacement optimal : ({delta_x}, {delta_y})")
        
        # Déplacement horizontal
        if delta_x > 0:
            self.orienter_vers('E')
        elif delta_x < 0:
            self.orienter_vers('W')
        
        # Si déplacement horizontal terminé, on se concentre sur le déplacement vertical
        if current_x == target_x:
            if delta_y > 0:
                self.orienter_vers('S')
            elif delta_y < 0:
                self.orienter_vers('N')
        
        # Une fois orienté, avance
        self.player.avance()

    def calculate_toric_distance(self, current, target, dimension_size):
        """Calcule la distance torique la plus courte entre deux points."""
        direct_distance = target - current
        if direct_distance > dimension_size // 2:
            return direct_distance - dimension_size
        elif direct_distance < -dimension_size // 2:
            return direct_distance + dimension_size
        return direct_distance

    def orienter_vers(self, direction):
        """Oriente le joueur vers la direction désirée en choisissant le sens de rotation optimal."""
        print(f"Orientation du joueur vers {direction}")
        directions = ['N', 'E', 'S', 'W']  # Ordre des directions
        current_index = directions.index(self.player.direction)
        target_index = directions.index(direction)

        # Calcul du nombre de rotations à droite et à gauche
        rotations_droite = (target_index - current_index) % len(directions)
        rotations_gauche = (current_index - target_index) % len(directions)

        # Choisir la rotation la plus courte
        if rotations_droite <= rotations_gauche:
            for _ in range(rotations_droite):
                self.player.droite()
        else:
            for _ in range(rotations_gauche):
                self.player.gauche()

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
