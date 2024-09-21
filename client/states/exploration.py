class Exploration(State):
    def __init__(self, player, grid_size=5):
        self.player = player
        self.grid_size = 2 + player.level
        self.grids = self.generate_grids()
        self.current_grid = None
        self.middle_coords = None

    def enter_state(self):
        print(f"Je suis en état {color('Exploration', 'blue')}")
        if self.player.focus_coords:
            self.middle_coords = self.player.focus_coords
            return
        self.current_grid = self.find_next_grid()
        if self.current_grid:
            self.middle_coords = self.get_middle_of_grid(self.current_grid)
        # else:
        #     print("Toutes les grilles sont explorées.")

    def exit_state(self):
        print(f"Sorti de l'état {color('Exploration', 'blue')}")
        pass
    
    def update(self) -> State:
        """Update pour le cycle d'exploration."""
        print(self.player.map_memory)
        print(f"{self.player.coordinates} not in view : {color(self.player.coordinates not in self.player.view, 'red')}")
        if self.player.coordinates not in self.player.view:
            self.explore_grid_center()
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
        """Find the next grid to explore based on memory scores."""
        highest_score = -1
        best_grid = None

        for grid_center in self.grids:
            grid_score = self.calculate_grid_score(grid_center)
            if grid_score > highest_score and self.player.has_enough_food(self.distance_toric(grid_center)):
                highest_score = grid_score
                best_grid = grid_center

        if best_grid:
            print(f"Next prioritized grid: {best_grid} with a score of {highest_score}")
        else:
            # If no prioritized grid, choose the best grid based on local scores
            best_grid = self.find_best_exploration_zone()
            print(f"Default chosen grid: {best_grid}")

        return best_grid

    def calculate_grid_score(self, grid_center):
        """Calculate the total score of a grid based on memory of tiles in the grid."""
        x_center, y_center = grid_center
        half_size = self.grid_size // 2
        total_score = 0

        for dx in range(-half_size, half_size + 1):
            for dy in range(-half_size, half_size + 1):
                x = (x_center + dx) % self.player.map_size[0]
                y = (y_center + dy) % self.player.map_size[1]
                tile_coords = (x, y)
                total_score += self.player.map_memory.get(tile_coords, 0)
        
        return total_score

    def find_best_exploration_zone(self):
        """Find the best exploration zone based on available grids."""
        best_grid = None
        best_score = 0

        for coords in self.grids:
            score = self.evaluate_grid(coords)
            if score > best_score and self.player.has_enough_food(self.distance_toric(coords)):
                best_score = score
                best_grid = coords

        return best_grid

    def evaluate_grid(self, coords):
        """Evaluate a grid based on found resources."""
        # Calculate the total score of resources in the grid
        x_center, y_center = coords
        half_size = self.grid_size // 2
        total_score = 0

        for dx in range(-half_size, half_size + 1):
            for dy in range(-half_size, half_size + 1):
                x = (x_center + dx) % self.player.map_size[0]
                y = (y_center + dy) % self.player.map_size[1]
                tile_coords = (x, y)
                total_score += self.player.map_memory.get(tile_coords, 0)
        
        return total_score

    def is_grid_explored(self, grid_start):
        """Check if an entire grid is explored."""
        x_start, y_start = grid_start
        for x in range(x_start, x_start + self.grid_size):
            for y in range(y_start, y_start + self.grid_size):
                if (x, y) not in self.player.view:
                    return False  # There are still unexplored tiles
        return True  # The entire grid is explored

    def get_middle_of_grid(self, grid_start):
        print(f"Calculating middle of grid {grid_start}")
        """Calculate the coordinates of the middle of the grid and check if they are explored."""
        x_start, y_start = grid_start
        middle_coords = ((x_start + self.grid_size // 2) % self.player.map_size[0]
                         , (y_start + self.grid_size // 2) % self.player.map_size[1])
        print(f"Middle of grid: {middle_coords}")
        if middle_coords not in self.player.view:
            print(f"Middle of grid not explored: {middle_coords}")
            return middle_coords
        print(f"Middle of grid already explored: {middle_coords}")
        # If the middle is already explored, find another unexplored tile
        for x in range(x_start, (x_start + self.grid_size) % self.player.map_size[0]):
            for y in range(y_start, (y_start + self.grid_size) % self.player.map_size[1]):
                if (x, y) not in self.player.view:
                    print(f"Unexplored tile found: {(x, y)}")
                    return (x, y)
        return None

    def explore_grid_center(self):
        """Explore the center of the grid by turning around."""
        print("Exploring grid center")
        self.player.voir()  # Look in the initial direction
        for _ in range(3):
            self.player.droite()  # Turn right
            self.player.voir()  # Look in the new direction
