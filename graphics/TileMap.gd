extends TileMap

const Content: Dictionary = {
	LINEMATE = "Linemate",
	DERAUMERE = "Deraumere",
	SIBUR = "Sibur",
	MENDIANE = "Mendiane",
	PHIRAS = "Phiras",
	THYSTAME = "Thystame",
	PLAYER = "Player",
	FOOD = "Food",
}

# const Tile: Dictionary = {
# 	LINEMATE = Vector2i(0, 6),
# 	DERAUMERE = Vector2i(3, 3),
# 	SIBUR = Vector2i(3, 0),
# 	MENDIANE = Vector2i(10, 9),
# 	PHIRAS = Vector2i(3, 9),
# 	THYSTAME = Vector2i(8, 5),
# 	PLAYER = Vector2i(0, 0),
# 	FOOD = Vector2i(4, 5),
# }

const FloorTile: Dictionary = {
	
}


const Tile: Dictionary = {
	LINEMATE = Vector2i(1,1),
	DERAUMERE = Vector2i(3, 1),
	SIBUR = Vector2i(0,1),
	MENDIANE = Vector2i(2,1),
	PHIRAS = Vector2i(6,1),
	THYSTAME = Vector2i(4, 1),
	PLAYER = Vector2i(0, 0),
	FOOD = [Vector2i(2,11), Vector2i(3,11), Vector2i(4 ,11), Vector2i(5 ,11)],
	EGG = Vector2i(4 ,10)
}

const items_source_id: int = 1
const floors_source_id: int = 0 

const MAP_JSON: JSON = preload ("res://cuicui.json")

var __NOmap: Array = MAP_JSON.data

var map: Array

#func map_json_string() -> String:
	#print(CUICUI)

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass


enum Terrain {
	SAND = 0,
	LIGHT_GRASS = 1,
	DARK_GRASS = 2
}

var nb_col: int = 0
var nb_row: int = 0

func init_map_tiling() -> void:
	for col: Array in map:
		nb_col += 1
		for row: Dictionary in col:
			#print(row)
			var x: int = row.p.x
			var y: int = row.p.y
			var pos: Vector2i = Vector2i(x, y)
			var content: Array = row.c
			if content.size() == 0:
				#set_cell(0, pos, floors_source_id, Vector2i(1,1))
				sand_cells.push_back(pos)
			else:
				light_grass_cells.push_back(pos)
			manage_cell_content(pos, content)
	set_cells_terrain_connect(0, sand_cells, 0, Terrain.SAND, false )
	set_cells_terrain_connect(0, light_grass_cells, 0, Terrain.LIGHT_GRASS, false )
	#set_cells_terrain_connect(0, [Vector2i(-10, 10)], 0, Terrain.LIGHT_GRASS, false )


var sand_cells: Array[Vector2i]
var light_grass_cells: Array[Vector2i]

func manage_cell_content(pos: Vector2i, content: Array) -> void:
	#var output: String = ""
	var layer: int = 1
	
	if content.size() == 0:
		set_cell(layer, pos, - 1)
		print("cell removed")
	else:
		print("cell add")
	for el: Dictionary in content:

		if el.is_empty():
			continue
			
		
		
		

		if el.has(Content.FOOD):
			set_cell(layer, pos, items_source_id, Tile.FOOD.pick_random() as Vector2i)
			# output += Content.FOOD + ": " + str(el[Content.FOOD]) + ", "
		if el.has(Content.DERAUMERE):
			set_cell(layer, pos, items_source_id, Tile.DERAUMERE)
			# output += Content.DERAUMERE + ": " + str(el[Content.DERAUMERE]) + ", "
		if el.has(Content.LINEMATE):
			set_cell(layer, pos, items_source_id, Tile.LINEMATE)
			# output += Content.LINEMATE + ": " + str(el[Content.LINEMATE]) + ", "
		if el.has(Content.MENDIANE):
			set_cell(layer, pos, items_source_id, Tile.MENDIANE)
			# output += Content.MENDIANE + ": " + str(el[Content.MENDIANE]) + ", "
		if el.has(Content.PHIRAS):
			set_cell(layer, pos, items_source_id, Tile.PHIRAS)
			# output += Content.PHIRAS + ": " + str(el[Content.PHIRAS]) + ", "
		if el.has(Content.SIBUR):
			set_cell(layer, pos, items_source_id, Tile.SIBUR)
			# output += Content.SIBUR + ": " + str(el[Content.SIBUR]) + ", "
		if el.has(Content.THYSTAME):
			set_cell(layer, pos, items_source_id, Tile.THYSTAME)
			# output += Content.THYSTAME + ": " + str(el[Content.THYSTAME]) + ", "
		if el.has(Content.PLAYER):
			set_cell(layer, pos, items_source_id, Tile.PLAYER)
			# output += Content.PLAYER + ": " + str(el[Content.PLAYER]) + ", "

	#print(output)

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func _on_network_map_ready(map_p: Array) -> void:
	map = map_p
	init_map_tiling()
	#print("network map: ", map_p[0])

func update_cells(cells: Array) -> void:
	for cell: Dictionary in cells:
		var pos: Vector2i = Vector2i(cell.p.x as int, cell.p.y as int)
		var content: Array = cell.c
		map[pos.x][pos.y].c = content
		manage_cell_content(pos, content)
		print("content: ", content)

func update_players(players: Array) -> void:
	for player: Dictionary in players:
		pass

func update_eggs(eggs: Array) -> void:
	for egg: Dictionary in eggs:
		pass

func _on_network_map_update(data: Dictionary) -> void:
	var cells: Array = data.cells
	var players: Array = data.players
	var eggs: Array = data.eggs
	
	update_cells(cells)
	update_players(players)
	update_eggs(eggs)
	
	print("updaye: ", data)
	print()
	print()
