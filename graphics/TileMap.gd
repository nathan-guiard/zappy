extends TileMap
class_name EnhancedTileMap
@onready var v_box_container_contents: VBoxContainer = %CanvasLayer/PanelContainer/MarginContainer/VBoxContainerContents
@onready var panel_container: PanelContainer = %CanvasLayer/PanelContainer
@onready var panel_players: PanelContainer = $"../CanvasLayer/PanelContainer2"
@onready var panel_container_inventory: PanelContainer = $"../CanvasLayer/PanelContainerInventory"
@onready var team_h_box_container: HBoxContainer = $"../CanvasLayer/TeamScrollContainer/TeamHBoxContainer"

@onready var v_box_container_players: VBoxContainer = %VBoxContainerPlayers
const player_info_btn_scene: PackedScene = preload("res://PlayerInfoBtn.tscn")
@onready var v_box_container_inventory: VBoxContainer = %VBoxContainerInventory

@onready var hover_square: Node2D = $"HoverSquare"
const content_info_row_scene: PackedScene = preload("res://ContentInfoRow.tscn")
#@onready var sprite_2d: Sprite2D = $CanvasLayer/Sprite2D
#@onready var texture_rect: TextureRect = $CanvasLayer/PanelContainer/MarginContainer/GridContainer/TextureRect
@onready var camera: EnhancedCamera2D = $"../Camera2D"

var _players: Dictionary = {}
#@onready var grid_container: GridContainer = $CanvasLayer/PanelContainer/MarginContainer/GridContainer
@onready var main: Node2D = $".."
const trace_square: PackedScene = preload("res://trace_square.tscn")

@onready var traces_square: Node2D = $TracesSquare
var traces_square_dic: Dictionary = {}


const TEAM_COLORS: Array = [
	Color(255, 0, 0),
	Color(0, 255, 0),
	Color(0, 0, 255),
	Color(0, 255, 255),
]

#teamone = Color(255,0,0)
var teams_color: Dictionary = {

}

const Content: Dictionary = {
	LINEMATE = "Linemate",
	DERAUMERE = "Deraumere",
	SIBUR = "Sibur",
	MENDIANE = "Mendiane",
	PHIRAS = "Phiras",
	THYSTAME = "Thystame",
	PLAYER = "Player",
	FOOD = "Food",
	EGG = "Egg",
}

#var _tiles_minerals_data: Array[Array]
var _tiles_data: Dictionary
#_tiles_minerals_data[0][1] = [
	#{
		#content =  "Linemate",
		#amount = 3
	#},
	#{
		#content = "Thystame",
		#amount = 4
	#}
#]
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
	LINEMATE = Vector2i(1, 1),
	DERAUMERE = Vector2i(3, 1),
	SIBUR = Vector2i(0, 1),
	MENDIANE = Vector2i(2, 1),
	PHIRAS = Vector2i(6, 1),
	THYSTAME = Vector2i(4, 1),
	PLAYER = Vector2i(4, 6),
	#FOOD = [Vector2i(1, 11), Vector2i(2,11), Vector2i(3,11), Vector2i(4 ,11), Vector2i(5 ,11)],
	FOOD = [Vector2i(4, 11), Vector2i(5, 11)],
	FOOD_1 = Vector2i(1, 11),
	EGG = Vector2i(4, 10)
}

var _tiles_texture: Dictionary = {
	
}

const items_source_id: int = 1
const floors_source_id: int = 0

const MAP_JSON: JSON = preload("res://cuicui.json")

var __NOmap: Array = MAP_JSON.data

var map: Array


var traces_square_overlaps_count: Dictionary = {}
#{
#	Vector2i(1,2) = 5

#}

var see_traces_of_players: bool = false

func _ready() -> void:

	const TILESET: TileSet = preload("res://tileset.tres")
	
	var atlas: TileSetAtlasSource = TILESET.get_source(1) as TileSetAtlasSource
	var atlas_image: Image = atlas.texture.get_image()
	#var tileImage: Image = atlasImage.get_region(atlas.get_tile_texture_region(Vector2i(0,2)))
	#var tiletexture: ImageTexture = ImageTexture.create_from_image(tileImage) 
	
	for k: String in Content:
		if k == "PLAYER":
			continue
		var tile_image: Image = atlas_image.get_region(atlas.get_tile_texture_region(Tile[k if k != "FOOD" else "FOOD_1"] as Vector2i))
		var tile_texture: ImageTexture = ImageTexture.create_from_image(tile_image)
		_tiles_texture[Content[k]] = tile_texture
	
	# print(_tiles_texture)
	#sprite_2d.texture = _tiles_texture["Sibur"]
	#texture_rect.texture = _tiles_texture["Sibur"]
	var texture_rect2: TextureRect = TextureRect.new()
	texture_rect2.texture = _tiles_texture["Linemate"]
	#ResourceSaver.save(_tiles_texture["Linemate"] as ImageTexture, "linemate_texture.res", 1)
	#grid_container.add_child(texture_rect2)
	
	var label_mineral: Label = Label.new()
	label_mineral.text = "Sibur"
	#grid_container.add_child(label_mineral)
	
	var label_amount: Label = Label.new()
	label_amount.text = "3"
	#grid_container.add_child(label_amount)


enum Terrain {
	SAND = 0,
	LIGHT_GRASS = 1,
	DARK_GRASS = 2
}

var nb_col: int = 0
var nb_row: int = 0

func _use_tile_data_runtime_update(layer: int, coords: Vector2i) -> bool:
	if layer > 0:
		return true
	return false
	
func _tile_data_runtime_update(layer: int, coords: Vector2i, tile_data: TileData) -> void:
	#print("_tile_data_runtime_update")
	return

func init_map_tiling() -> void:
	for col: Array in map:
		nb_col += 1
		for row: Dictionary in col:
			if nb_col == 1:
				nb_row += 1
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
	set_cells_terrain_connect(0, sand_cells, 0, Terrain.SAND, false)
	set_cells_terrain_connect(0, light_grass_cells, 0, Terrain.LIGHT_GRASS, false)
	init_outside_map()


var sand_cells: Array[Vector2i]
var light_grass_cells: Array[Vector2i]

var dark_grass_cells: Array[Vector2i]


var outside_dark_grass_cells: Array[Vector2i]


func init_outside_map() -> void:
	var i: int = -nb_col
	var j: int = -nb_row
	# print("i: ", i)
	# print("j: ", j)
	while i < nb_col * 2:
		j = -nb_row
		while j < nb_row * 2:
			if not (i >= 0 and i < nb_col and j >= 0 and j < nb_row):
				outside_dark_grass_cells.push_back(Vector2i(i, j))
			j += 1
		i += 1
	#print("olala: ",outside_dark_grass_cells)
	set_cells_terrain_connect(0, outside_dark_grass_cells, 0, Terrain.DARK_GRASS, false)
		

func is_there_food(content: Array) -> bool:
	for el: Dictionary in content:
		if el.has(Content.FOOD):
			return true
	return false

func is_there_minerals(content: Array) -> bool:
	for el: Dictionary in content:
		if el.has(Content.DERAUMERE) or el.has(Content.LINEMATE) or el.has(Content.MENDIANE) or el.has(Content.PHIRAS) or el.has(Content.SIBUR) or el.has(Content.THYSTAME):
			return true
	return false


func update_tiles_data(pos: Vector2i, content: Array) -> void:
	_tiles_data[pos] = content

func manage_cell_content(pos: Vector2i, content: Array) -> void:
	#var output: String = ""
	var food_layer: int = 1
	var minerals_layer: int = 2
	#print(content)
	update_tiles_data(pos, content)
	
	if not is_there_food(content):
		set_cell(food_layer, pos, -1)
	if not is_there_minerals(content):
		set_cell(minerals_layer, pos, -1)
		

	#print("content: ", content)
	#print()
	for el: Dictionary in content:

		if el.is_empty():
			continue

		if el.has(Content.FOOD):
			set_cell(food_layer, pos, items_source_id, Tile.FOOD.pick_random() as Vector2i)
		
			
			# output += Content.FOOD + ": " + str(el[Content.FOOD]) + ", "
		if el.has(Content.DERAUMERE):
			set_cell(minerals_layer, pos, items_source_id, Tile.DERAUMERE)
			# output += Content.DERAUMERE + ": " + str(el[Content.DERAUMERE]) + ", "
		if el.has(Content.LINEMATE):
			set_cell(minerals_layer, pos, items_source_id, Tile.LINEMATE)
			# output += Content.LINEMATE + ": " + str(el[Content.LINEMATE]) + ", "
		if el.has(Content.MENDIANE):
			set_cell(minerals_layer, pos, items_source_id, Tile.MENDIANE)
			# output += Content.MENDIANE + ": " + str(el[Content.MENDIANE]) + ", "
		if el.has(Content.PHIRAS):
			set_cell(minerals_layer, pos, items_source_id, Tile.PHIRAS)
			# output += Content.PHIRAS + ": " + str(el[Content.PHIRAS]) + ", "
		if el.has(Content.SIBUR):
			set_cell(minerals_layer, pos, items_source_id, Tile.SIBUR)
			# output += Content.SIBUR + ": " + str(el[Content.SIBUR]) + ", "
		if el.has(Content.THYSTAME):
			set_cell(minerals_layer, pos, items_source_id, Tile.THYSTAME)
			# output += Content.THYSTAME + ": " + str(el[Content.THYSTAME]) + ", "
		#if el.has(Content.PLAYER):
			#set_cell(layer + 1, pos, items_source_id, Tile.PLAYER)
			
			# output += Content.PLAYER + ": " + str(el[Content.PLAYER]) + ", "


func _on_network_map_ready(map_p: Array) -> void:
	map = map_p
	init_map_tiling()
	#print("network map: ", map_p[0])

func update_cells(cells: Array) -> void:
	dark_grass_cells = []
	for cell: Dictionary in cells:
		var pos: Vector2i = Vector2i(cell.p.x as int, cell.p.y as int)
		var content: Array = cell.c
		map[pos.x][pos.y].c = content
		manage_cell_content(pos, content)
		#print("content: ", content)
		
		if content.size() == 0:
			dark_grass_cells.push_back(pos)
	set_cells_terrain_connect(0, dark_grass_cells, 0, Terrain.DARK_GRASS, false)

var count: int = 0
func update_players(players: Array) -> void:
	count += 1
	if count % 10 == 0:
		#print()
		#print(players)
		#print()
		#print()
		pass
	#print("plaayers: ", players)
	prune_players(players)
	for player_info_btn: Node in v_box_container_players.get_children():
		player_info_btn.queue_free()
	merge_players(players)
	for player_id: int in _players:
		var player: Player = _players[player_id]
		#player.animate()
		update_position_player_on_map(player)
		player.refresh_action_label()
		player.refresh_level_color()
		
		if camera.focused_player == player:
			if camera.focused_player:
				panel_container_inventory.visible = true
			update_contents_in_v_box_ctn(v_box_container_inventory, player.inventory)
		if not teams_color.has(player.team):
			teams_color[player.team] = TEAM_COLORS[teams_color.size()]
			var new_label: Label = Label.new()
			new_label.text = player.team
			new_label["theme_override_colors/font_color"] = teams_color[player.team]
			new_label["theme_override_font_sizes/font_size"] = 45
			team_h_box_container.add_child(new_label)
		
		var player_info_btn: PlayerInfoBtn = player_info_btn_scene.instantiate()
		v_box_container_players.add_child(player_info_btn)
		player_info_btn.info = "Level " + str(player.level)
		player_info_btn.logo = player.anim.sprite_frames.get_frame_texture("down_walk", 0)
		player_info_btn.logo_color = teams_color[player.team]
		player_info_btn.player_id = player.id
		player_info_btn.button_down.connect(_on_player_info_btn_button_down.bind(player.id))
		
		if player.team_color == Color(0, 0, 0):
			player.team_color = teams_color[player.team]
		
		#print("action: ", new_player.action)
	#print("_players: ", _players)

func update_eggs(eggs: Array) -> void:
	#print("eggs: ", eggs)
	for egg: Dictionary in eggs:
		pass

func _on_network_map_update(data: Dictionary) -> void:
	var cells: Array = data.cells
	var players: Array = data.players
	var eggs: Array = data.eggs
	
	update_cells(cells)
	update_eggs(eggs)
	update_players(players)
	
	#print("updaye: ", data)
	#print()
	#print()
const player_scene: PackedScene = preload("res://player.tscn")
static func construct_player_from_dictionnary(dic: Dictionary) -> Player:
	var new_player: Player = player_scene.instantiate()
	new_player.map_pos = Vector2i(dic.position.x as int, dic.position.y as int)
	new_player.direction = dic.direction
	new_player.team = dic.team
	new_player.inventory = dic.inventory
	new_player.level = dic.level
	new_player.action = JSON.stringify(dic.action)
	new_player.id = dic.id

	#print( new_player.direction)
	return new_player


static func update_player_from_dictionnary(player: Player, dic: Dictionary) -> void:
	player.map_pos = Vector2i(dic.position.x as int, dic.position.y as int)
	#print("player.map_pos: ", player.map_pos)
	player.direction = dic.direction
	player.team = dic.team
	player.inventory = dic.inventory
	player.level = dic.level
	player.action = JSON.stringify(dic.action)
	
	#print("level: ", player.level)


func update_position_player_on_map(player: Player) -> void:
	player.destination = to_global(map_to_local(player.map_pos))
	# player.map_position_history.push_back(player.map_pos)


func prune_players(remote_players: Array) -> void:
	for player_id: int in _players:
		var player_exist: bool = false
		for remote_player: Dictionary in remote_players:
			if int(remote_player.id as float) == player_id:
				player_exist = true
		if not player_exist:
			(_players[player_id] as Player).queue_free()
			_players.erase(player_id)


func merge_players(remote_players: Array) -> void:
	for remote_player: Dictionary in remote_players:
		#print(type_string(typeof(remote_player.id)))
		var remote_player_id: int = remote_player.id
		if not _players.has(remote_player_id):
			var new_player: Player = construct_player_from_dictionnary(remote_player)
			_players[remote_player_id] = new_player
			new_player.new_map_position_added.connect(_on_player_new_map_position_added)
			add_child(new_player)
			#print("player added")
		var player: Player = _players[remote_player_id]
		update_player_from_dictionnary(player, remote_player)


func _on_timer_notify_timeout() -> void:
	#print("timer !")
	#notify_runtime_tile_data_update(0)
	pass


func _unhandled_input(event: InputEvent) -> void:
	#print(event)
	var hovered_cell: Vector2i = local_to_map(get_local_mouse_position())
	if not _tiles_data.has(hovered_cell):
		return
	var data: Array = _tiles_data[hovered_cell]
	if event is InputEventMouseMotion:
		var ev: InputEventMouseMotion = event
		hover_square.position = map_to_local(hovered_cell)

		var data_filtered: Array = data_without_player(data)
		update_contents_in_v_box_ctn(v_box_container_contents, data_filtered)
				
		#print(ev.as_text_keycode())
	#camera.manage_camera_input(event)
	if event is InputEventKey:
		var ev: InputEventKey = event
		if ev.is_pressed() and ev.keycode == KEY_A:
			camera.focused_player = null # L ORDRE DE SES DEUX LIGNES EST IMPORTANTE
			see_traces_of_players = !see_traces_of_players
			if see_traces_of_players:
				for curr_player_id: int in _players:
					for pos: Vector2i in _players[curr_player_id].map_position_history:
						add_trace_square(pos)


#var hovered_cell_data: TileData
#func _unhandled_input(event: InputEvent) -> void:
	#var hovered_cell: Vector2i = local_to_map(get_local_mouse_position())
	#var data: TileData = get_cell_tile_data(1, hovered_cell)
	#if not data:
		#return
	#if event is InputEventMouseMotion:
	#
		#var ev: InputEventMouseMotion = event
		#if hovered_cell_data:
			#hovered_cell_data.modulate = Color(1, 1, 1, 1)
		#
		#hovered_cell_data = data
		#hovered_cell_data.modulate = Color(1, 0, 0, 1)
		#print(data)
	#if event is InputEventMouseButton:
		#var ev: InputEventMouseButton = event
		#if ev.button_index == MOUSE_BUTTON_LEFT:
			#data.get_custom_data_by_layer_id(1)
	#if event is InputEventKey and event.is_pressed():
		#var ev: InputEventKey = event
		#data.set_custom_data_by_layer_id(1, ev.as_text_keycode())
		#print(ev.as_text_keycode())

func data_without_player(data: Array) -> Array:
	var new_data: Array[Dictionary] = []
	for el: Dictionary in data:
		if not el.has(Content.PLAYER):
			new_data.push_back(el)
	return new_data


func _on_player_info_btn_button_down(player_id: int) -> void:
	print("button pressed ! player_id: ", player_id)
	for curr_player_id: int in _players:
		# (_players[curr_player_id] as Player).toggle_outline(false)
		pass
	if _players.has(player_id):
		var player: Player = _players[player_id]
		camera.focus_player(player)
		# player.toggle_outline(true)


func clear_traces_square() -> void:
	for child: Node2D in traces_square.get_children():
		child.queue_free()
	traces_square_dic = {}

func add_trace_square(map_position: Vector2i) -> void:
	if not traces_square_dic.has(map_position):
		var new_trace_square: TraceSquare = trace_square.instantiate()
		new_trace_square.position = map_to_local(map_position)
		traces_square.add_child(new_trace_square)
		traces_square_dic[map_position] = new_trace_square
	else:
		(traces_square_dic[map_position] as TraceSquare).overlaps_count += 1

func update_contents_in_v_box_ctn(v_box_container: VBoxContainer, contents: Array) -> void:

	clear_contents_in_v_box_ctn(v_box_container)

	for content: Dictionary in contents:
		for key: String in content:
			if v_box_container.get_child_count() > 0:
				var h_separator: HSeparator = HSeparator.new()
				h_separator["theme_override_styles/separator"] = preload("res://sep_style.tres")
				v_box_container.add_child(h_separator)
			
			var content_info_row: ContentInfoRow = content_info_row_scene.instantiate()
			v_box_container.add_child(content_info_row)
			content_info_row.icon = _tiles_texture[key]
			content_info_row.key = key
			content_info_row.value = str(content[key])

func clear_contents_in_v_box_ctn(v_box_container: VBoxContainer) -> void:
	for child: Node in v_box_container.get_children():
		child.free()

func close_inventory() -> void:
	clear_contents_in_v_box_ctn(v_box_container_inventory)
	panel_container_inventory.visible = false
	

func _on_player_new_map_position_added(player: Player, map_position: Vector2i) -> void:
	if see_traces_of_players or camera.focused_player == player:
		add_trace_square(map_position)
