extends Camera2D
class_name EnhancedCamera2D

# Called when the node enters the scene tree for the first time.
@onready var tile_map: EnhancedTileMap = $"../TileMap"

var desired_zoom: Vector2 = Vector2(2.2, 2.2)

var follow_player: bool = true

var focused_player: Player = null:
	get:
		return focused_player if is_instance_valid(focused_player) else null
	set(new_val):
		if new_val == null:
			if focused_player:
				focused_player.toggle_outline(false)
			tile_map.clear_traces_square()
		focused_player = new_val



@onready var last_drag_position: Vector2 = Vector2()

var initial_position_smoothing_speed: float
@onready var line_2d: Line2D = %Line2D


func _ready() -> void:
	initial_position_smoothing_speed = position_smoothing_speed

func _process(delta: float) -> void:
	zoom = lerp(zoom, desired_zoom, 0.1)
	if zoom.x < 0.1:
		zoom = Vector2(0.1, 0.1)
	if zoom.y < 0.1:
		zoom = Vector2(0.1, 0.1)
	if focused_player and follow_player:
		global_position = focused_player.global_position
	
	
	

func _unhandled_input(event: InputEvent) -> void:

	if event is InputEventMouseMotion:
		var mouse_event: InputEventMouseMotion = event
		if Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
			if focused_player:
				follow_player = false
			var drag: Vector2 = last_drag_position - mouse_event.position
			global_position += drag
			last_drag_position = mouse_event.position
			# position_smoothing_speed = initial_position_smoothing_speed * 3
		else:
			last_drag_position = mouse_event.position
			# position_smoothing_speed = initial_position_smoothing_speed
		
	if event is InputEventMouseButton:
		#print("Mouse button pressed")
		var mouse_event: InputEventMouseButton = event
		if mouse_event.button_index == MOUSE_BUTTON_WHEEL_UP or Input.is_key_label_pressed(KEY_P):
			print("Zoom in")
			global_position = get_global_mouse_position()			
			desired_zoom = zoom * 1.2
		elif mouse_event.button_index == MOUSE_BUTTON_WHEEL_DOWN or Input.is_key_label_pressed(KEY_O):
			#print("Zoom out")
			desired_zoom = zoom * 0.8
		#elif mouse_event.button_index == MOUSE_BUTTON_LEFT:
			#global_position = get_global_mouse_position()
	if event is InputEventKey:
		var ev: InputEventKey = event
		if ev.is_pressed() and (ev.keycode == KEY_EQUAL or ev.keycode == KEY_W):
			desired_zoom = zoom * 1.2
		elif ev.is_pressed() and (ev.keycode == KEY_MINUS or ev.keycode == KEY_S):
			desired_zoom = zoom * 0.8 
		elif ev.is_pressed() and ev.keycode == KEY_ESCAPE:
			focused_player = null
		


func focus_position(position: Vector2) -> void:
	global_position = position
	focused_player = null


	
func focus_player(player: Player) -> void:
	focused_player = player
	follow_player = true
	print(focused_player)
