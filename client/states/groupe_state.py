
import time 
from states.group import Group
from states.color import color
from states.cluster_optimisation import find_cluster_center

import random

class GroupState:
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

    def distance_toric(self, destination, src=None):
        """Calcul la distance torique entre deux points."""
        if src is None:
            src = self.player.coordinates
        x1, y1 = src
        x2, y2 = destination
        dx = self.calculate_toric_distance(x1, x2, self.player.map_size[0])
        dy = self.calculate_toric_distance(y1, y2, self.player.map_size[1])
        return abs(dx) + abs(dy)


class Idle(GroupState):
    def __init__(self, player):
        self.player = player
        pass
    
    def enter_state(self):
        pass        
        
        
    
    def exit_state(self):
        # print("\n\n")
        # print("Idle exit_state\n\n")
        pass
    
    def update(self):
        if self.player.level == 8:
            return MaximumLevelReached(self.player)
        
        # Si j'ai pas assez de nourriture, je vais chercher de la nourriture
        self.player.inventaire()
        self.player.voir()
        self.player.communicate()
        
        self.player.fork_manager()
        
        if self.player.inventory.get("Food", 0) < 2000:
            return Nourrir(self.player)
        
        if self.player.groups:
            self.required_ressources = self.player.groups.missing_ressources()
            # print("Ressources manquantes: ", self.required_ressources)


        # print("Group: ", self.player.groups)
        if self.player.groups is None:
            return Group_research(self.player)
        
        # self.player.display_info()
        
        # print("Group id: ", self.player.groups.id)
        
        # print("Group members: ", self.player.groups.members)
        # print(f"groups ressources: ", self.player.groups.ressources)
        # print("Missing ressources: ", self.required_ressources)
        # print("Ressources needed: ", self.player.groups.needed_ressources)
        
        
        if not self.player.groups.enougth_players():
            return Group_members_search(self.player)
        
        if self.player.focus_coords is None and self.required_ressources:
            self.player.focus_coords = self.choisir_meilleure_case()
        
        if self.required_ressources is None:
            return Incantation(self.player)
        elif self.player.focus_coords and self.player.focus_coords != self.player.coordinates:
            return Deplacement(self.player, self.player.focus_coords)
        elif self.player.coordinates == self.player.focus_coords:
            return Recolte(self.player)
        return Exploration(self.player)
    
    def level_up_ressources(self, resources):
        """Détermine les ressources à récolter pour le level up."""
        required_ressources = {}
        for ressource, quantity in self.required_ressources.items():
            if ressource in resources:
                available_quantity = resources[ressource]
                required_ressources[ressource] = min(quantity, available_quantity)
        return required_ressources
    
    def choisir_meilleure_case(self):
        """Choisit la meilleure case en fonction des ressources manquantes"""
        best_tile = None
        best_score = 0
        if self.required_ressources is None:
            return None
        for coords, resources in self.player.view.items():
            score = self.evaluate_tile(resources)
            if score > best_score and self.player.has_enough_food(self.distance_toric(coords)):
                best_score = score
                best_tile = coords
                self.player.focus_ressources = self.level_up_ressources(resources)
        # print(f"Meilleure case : {color(best_tile if best_score else 'None', 'red')} avec un score de {color(str(best_score), 'red')}")
        return best_tile
    
    def evaluate_tile(self, resources):
        """Évalue une case en fonction des ressources manquantes et retourne un score."""
        score = 0
        for resource, needed_quantity in self.required_ressources.items():
            if resource in resources:
                available_quantity = resources[resource]
                score += min(needed_quantity, available_quantity) * 10  # Pondération par ressource
        return score
 
 
class MaximumLevelReached(GroupState):
    def __init__(self, player):
        self.player = player

    def enter_state(self):
        # print(f"{color('Maximum Level Reached', 'red')} : Je suis au niveau maximum.")
        pass

    def exit_state(self):
        # print(f"{color('Maximum Level Reached', 'red')} : Je quitte l'état.")
        pass

    def update(self):
        self.player.inventaire()
        self.player.voir()
        
        if self.player.inventory.get("Food", 0) < 2000:
            return Nourrir(self.player)
        
        time.sleep(1)
        return None
 
class Group_research(GroupState):
    def __init__(self, player):
        self.player = player
        self.group = self.player.groups

    def enter_state(self):
        # print("Group_research enter_state")
        pass

    def exit_state(self):
        # print("Group_research exit_state")
        pass

    def update(self):
        # Regarde si un joueur recrute, sinon je cree mon groupe et je recrute
        if self.group is None:
            # print("memory idle", self.player.memory)
            for team_id, team_info in self.player.memory.items():
                if team_info.etat == "recrute" and team_info.level == self.player.level:
                    self.player.interested(team_id)
                    return Idle(self.player)
            self.player.create_group()
        return Idle(self.player)

class Group_members_search(GroupState):
    def __init__(self, player):
        self.player = player
        self.group = self.player.groups
    
    def enter_state(self):
        # print("Group_members_search enter_state")
        pass
    
    def exit_state(self):
        # print("Group_members_search exit_state")
        pass
    
    def update(self):
        # Si je suis la c'est que j'ai un groupe.
        # Je suis ou leader de groupe ou simple membre
        # Si je suis leader je recrute des membres
        # Si je suis membre je retourn en idle
        if self.group.id == self.player.id:
            # print("Je suis le leader")
            self.group.recrute()
        return Idle(self.player)


class Exploration(GroupState):
    def __init__(self, player):
        self.player = player
        self.grid_size = 2 + player.level
        self.grids = self.generate_grids()
        self.current_grid = None
        self.middle_coords = None
        self.cluster_point = None

    def enter_state(self):
        # Je cherche si je peux trouver un cluster point
        self.cluster_point = find_cluster_center(self.player.map_memory)
        # if self.cluster_point:
        #     print(f"Cluster point trouvé en {self.cluster_point}")

    def exit_state(self):
        pass
    
    def update(self) -> GroupState:
        """Mise à jour pour le cycle d'exploration."""
        # Si je n'ai jamais explore la case actuelle, je l'explore
        if self.player.coordinates not in self.player.view:
            self.view()
            return Idle(self.player)
        
        # Si j'ai un cluster_point, je me déplace vers ce point de manière biaisée
        if self.cluster_point:
            next_target = self.biased_random_walk()
            if next_target: 
                return Deplacement(self.player, next_target)
        
        # Scénario sans cluster point
        unexplored_tiles = self.get_unexplored_tiles()
        if unexplored_tiles:
            return Deplacement(self.player, unexplored_tiles)

        # Si toute la carte est explorée, réinitialiser l'exploration
        self.reset_exploration()
        return Idle(self.player)

    def biased_random_walk(self):
        """Sélectionne un point autour du cluster point avec une probabilité plus forte."""

        radius = 10  # Rayon de 10 cases autour du cluster point
        candidate_points = [
            (self.cluster_point[0] + x, self.cluster_point[1] + y)
            for x in range(-radius, radius + 1)
            for y in range(-radius, radius + 1)
            if 0 <= (self.cluster_point[0] + x) < self.player.map_size[0] and
               0 <= (self.cluster_point[1] + y) < self.player.map_size[1]  # S'assurer que le point est dans la carte
        ]

        # Biaisé en faveur des points proches du cluster
        weighted_points = []
        for point in candidate_points:
            distance = self.distance_toric(point, self.cluster_point)
            weight = 1 / (distance + 1)  # Plus le point est proche, plus le poids est élevé
            weighted_points.append((point, weight))

        # Normalisation des poids
        total_weight = sum(weight for _, weight in weighted_points)
        normalized_points = [(point, weight / total_weight) for point, weight in weighted_points]

        # Sélectionne un point selon la distribution des probabilités
        selected_point = random.choices([point for point, _ in normalized_points],
                                        [weight for _, weight in normalized_points])[0]

        return selected_point

    def generate_grids(self):
        """Génère une liste des centres des grilles sur la carte."""
        grids = []
        map_width, map_height = self.player.map_size
        
        for x in range(0, map_width, self.grid_size):
            for y in range(0, map_height, self.grid_size):
                grids.append((x, y))
        
        random.shuffle(grids)
        
        return grids

    def find_next_grid(self):
        """Trouve la prochaine grille non explorée en tenant compte de la distance."""
        best_grid = None

        for grid_start in self.grids:
            distance = self.distance_toric(grid_start, self.player.coordinates)
            if self.player.has_enough_food(distance):
                if not self.is_grid_explored(grid_start):
                    return grid_start
        
        return best_grid

    def is_grid_explored(self, grid_start):
        """Vérifie si une grille entière est explorée."""
        x_start, y_start = grid_start
        for x in range(x_start, x_start + self.grid_size):
            for y in range(y_start, y_start + self.grid_size):
                if (x, y) not in self.player.view:
                    return False  # Il reste des cases non explorées
        return True  # Toute la grille est explorée

    def get_middle_of_grid(self, grid_start):
        """Calcule les coordonnées du milieu de la grille."""
        x_start, y_start = grid_start
        middle_coords = ((x_start + self.grid_size // 2) % self.player.map_size[0],
                         (y_start + self.grid_size // 2) % self.player.map_size[1])
        return middle_coords

    def get_unexplored_tiles(self):
        """Renvoie une liste de cases non explorées."""
        unexplored_grid = self.find_next_grid()
        if unexplored_grid:
            return self.get_middle_of_grid(unexplored_grid)
        return None
    
    def view(self):
        """Explore le centre de la grille en tournant sur soi-même."""
        self.player.voir()  # Voir en direction initiale
        for _ in range(3):
            self.player.droite()  # Tourne à droite
            self.player.voir()  # Voir dans la nouvelle direction

    def reset_exploration(self):
        """Réinitialise l'exploration de la carte."""
        self.player.view.clear()  # Réinitialiser la vue du joueur



class Recolte(GroupState):
    def __init__(self, player):
        self.player = player

    def enter_state(self):
        # print(f"Je suis en état {color('RECOLTE', 'lightgreen')}")
        pass
    
    def exit_state(self):
        # self.player.display_info()
        self.player.focus_coords = None
        # print(f"Je suis sorti de l'état {color('RECOLTE', 'lightgreen')}")

    def update(self) -> GroupState:
        """Essaye de récolter les ressources de la case actuelle"""
        for ressource, quantity in self.player.focus_ressources.items():
            for _ in range(quantity):
                if self.player.prend(ressource):
                    break
        self.player.focus_ressources = None
        self.player.info()
        return Idle(self.player)


class Nourrir(GroupState):
    def __init__(self, player):
        self.player = player

    def enter_state(self):
        # print("Je suis en état Nourrir")
        self.target_coords = self.choisir_meilleure_case()
        self.player.focus_coords = self.target_coords
    
    def exit_state(self):
        # print("Je suis sorti de l'état Nourrir")
        pass
    
    def update(self) -> GroupState:
        """Update pour le cycle de nourrissage."""
        
        # Si le joueur a assez de nourriture, retourne à l'état Idle
        if self.player.inventory.get("Food", 0) >= 4000:
            self.player.focus_coords = None
            return Idle(self.player)
        
        # Si la case cible n'est pas définie, retourne à l'état Exploration
        if self.target_coords is None:
            return Exploration(self.player)
        
        # Si le joueur est sur la case cible, prend de la nourriture
        if self.player.coordinates == self.target_coords:
            if self.player.prend("Food"):
                return Nourrir(self.player)
            return None
        
        # Sinon, se déplace vers la case cible
        return Deplacement(self.player, self.target_coords)
    
    def choisir_meilleure_case(self):
        """Choisit la meilleure case en fonction des ressources manquantes et de la distance."""
        best_tile = None
        best_score = -1
        for coords, resources in self.player.view.items():
            score = self.evaluate_tile(resources, coords)
            if score > best_score and self.player.has_enough_food(self.distance_toric(coords)):
                best_score = score
                best_tile = coords
        return best_tile

    def evaluate_tile(self, resources, coords):
        """Évalue une case en fonction des ressources et de la distance."""
        score = 0
        # Pondération par ressource
        score = resources.get("Food", 0)

        # Calcul de la distance par rapport au joueur
        distance = self.distance_toric(coords)

        # Ajout d'un coefficient de distance (plus la distance est grande, plus le score est réduit)
        distance_coefficient = 1 / (distance + 1)  # Ajout de 1 pour éviter la division par zéro
        score *= distance_coefficient

        return score


class Deplacement(GroupState):
    def __init__(self, player, target_coords):
        self.player = player
        self.player.focus_coords = target_coords
        self.map_width, self.map_height = player.map_size

    def enter_state(self):
        # print(f"Je suis en état {color('DEPLACEMENT', 'pink')} vers {self.player.focus_coords}")
        if self.player.focus_coords is None:
            return
        if not self.player.has_enough_food(self.distance_toric(self.player.focus_coords)):
            self.player.focus_coords = None

    def exit_state(self):
        # print(f"J'ai atteint la cible {self.player.focus_coords}, sorti de l'état {color('DEPLACEMENT', 'pink')}")
        self.player.focus_coords = None
    
    def update(self) -> GroupState:
        if self.player.focus_coords is None:
            return Idle(self.player)
        
        if self.player.coordinates == self.player.focus_coords:
            # print(f"Joueur arrivé à la destination {self.player.focus_coords}")
            return Idle(self.player)  # Retour à l'état précédent ou un autre état
        
        self.move_to_target()
        return None  # Reste dans l'état Deplacement jusqu'à atteindre la cible

    def move_to_target(self):
        """Se déplace vers les coordonnées cibles en prenant en compte la carte torique."""
        current_x, current_y = self.player.coordinates
        target_x, target_y = self.player.focus_coords
        # print(f"Joueur en ({current_x}, {current_y}), cible en ({target_x}, {target_y})")
         
        # Calcul du déplacement optimal en tenant compte de la carte torique
        delta_x = self.calculate_toric_distance(current_x, target_x, self.map_width)
        delta_y = self.calculate_toric_distance(current_y, target_y, self.map_height)
        # print(f"Déplacement optimal : ({delta_x}, {delta_y})")
        
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
        
        # 30% chance d'appeler self.player.voir
        if random.random() <= 0.3:
            self.player.voir()
        
        # Une fois orienté, avance
        self.player.avance()

    def orienter_vers(self, direction):
        """Oriente le joueur vers la direction désirée en choisissant le sens de rotation optimal."""
        # print(f"Orientation du joueur vers {direction}")
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

        # print(f"Joueur orienté vers {direction}")
    
class Incantation(GroupState):
    def __init__(self, player):
        self.player = player

    def enter_state(self):
        # print("Je suis en état INCANTATION")
        pass

    def exit_state(self):
        # print("Je suis sorti de l'état INCANTATION")
        pass

    def update(self) -> GroupState:
        
        # Si je ne suis pas aux coordonnes du groups alors je me deplace
        if self.player.coordinates != self.player.groups.coords:
            return Deplacement(self.player, self.player.groups.coords)
        
        # print(f"{color('Incantation', 'red')} : Je suis aux coordonnées du groupe")
        
        # Si je suis aux coordonnes du groupe alors je vide mon inventaire et j'incante
        for k, v in self.player.inventory.items():
            if k == "Food":
                continue
            for _ in range(v):
                self.player.pose(k)
        if self.player.incantation():
            self.player.voir()
            self.player.info()
            return Idle(self.player)
        
        self.player.fork()
        self.player.stop()
        # Implémentez la logique de l'incantation ici
        return Idle(self.player)

