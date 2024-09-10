extends Node2D
class_name Player

	# "position": GamePosition,
	# "direction": string, // see below
	# "team": string,
	# "action": string or object, // see below
	# "inventory": [GameCellContent],
	# "state": string or object, // see below
	# "level": number,

signal new_map_position_added(player: Player, map_position: Vector2i)

@onready var outline_shader: ShaderMaterial = preload("res://player_shader.tres").duplicate()

@onready var team_color: Color = Color(0,0,0):
	set(val):
		team_color = val
		outline_shader.set_shader_parameter("outline_color", team_color)


@onready var animations: Array[AnimatedSprite2D] = [$level_1, $level_2, $level_3, $level_4, $level_5, $level_6, $level_7, $level_8]
@onready var action_label: RichTextLabel = %ActionLabel
@onready var polygon_2d: Polygon2D = %Polygon2D

@onready var anim: AnimatedSprite2D:
	get:
		return animations[clamp(level - 1, 0, 7)]

var id: int = 0

const INITIAL_LERP_SPEED: float = 3
var lerp_speed: float = INITIAL_LERP_SPEED

#var position_history: PackedVector2Array = PackedVector2Array()

var map_position_history: PackedVector2Array = PackedVector2Array()

var destination: Vector2:
	set(new_dest):
		destination = new_dest
		#position_history.push_back(destination)

const Direction: Dictionary = {
	"North": "North",
	"South": "South",
	"East": "East",
	"West": "West"
}

const Action: Dictionary = {
	"Avance": "aod"
}

var map_pos: Vector2i:
	set(new_pos):
		map_pos = new_pos
		if map_position_history.size() == 0 or Vector2i(map_position_history[map_position_history.size() - 1]) != map_pos:
			map_position_history.push_back(map_pos)
			new_map_position_added.emit(self, map_pos)
@onready var direction: String
				
var team: String
var inventory: Array:
	set(new_arr):
		inventory = new_arr
		print("inventory: ", inventory)
var level: int = 1:
	set(val):
		(get_node("level_" + str(level)) as AnimatedSprite2D).visible = false
		level = val
		(get_node("level_" + str(level)) as AnimatedSprite2D).visible = true
var action: String

#func move(direction: Vector2i) -> void:
	#position += direction

var WalkAnim: Dictionary  = {
	UP = "up_walk",
	DOWN = "down_walk",
	RIGHT = "right_walk",
	LEFT = "left_walk"
}

var WalkAnimArray: Array = [ WalkAnim.UP, WalkAnim.DOWN, WalkAnim.RIGHT, WalkAnim.LEFT]

func animate_walk() -> void:
	match direction:
		"North":
			anim.play(WalkAnim.UP as StringName)
		"South":
			anim.play(WalkAnim.DOWN as StringName)
		"East":
			anim.play(WalkAnim.RIGHT as StringName)
		"West":
			anim.play(WalkAnim.LEFT as StringName)

func refresh_action_label() -> void:
	action_label.text = "[center]" + action + "[/center]"
	
func refresh_level_color() -> void:
# 	1 - ffffff

# 2 - 000000

# 3 - ff0000

# 4 - 00ff00

# 5 - 0000ff

# 6 -  555555

# 7 - 555555

# 8 - 555555
	match level:
		1:
			polygon_2d.color = Color("#ffffff")
		2:
			polygon_2d.color = Color("#000000")
		3:
			polygon_2d.color = Color("#ff0000")
		4:
			polygon_2d.color = Color("#00ff00")
		5:
			polygon_2d.color = Color("#0000ff")
		6:
			polygon_2d.color = Color("#555555")
		7:
			polygon_2d.color = Color("#555555")
		8:
			polygon_2d.color = Color("#555555")
		_:
			polygon_2d.color = Color("#ffffff")


func _physics_process(delta: float) -> void:
	global_position = global_position.lerp(destination, clampf(lerp_speed * delta, 0.0, 1.0))
	if global_position.distance_to(destination) > 2:
		animate_walk()
		#print("animation playing")
		#print(global_position.distance_to(destination))
	elif WalkAnimArray.has(anim.animation):
		anim.stop()
		#print("animation stopped ")

var tween_scale: Tween

func _ready() -> void:
	lerp_speed = 100.0
	visible = false
	tween_scale = get_tree().create_tween()
	tween_scale.tween_callback(func() -> void:
		visible = true
	)
	tween_scale.tween_property(self, "scale", Vector2(5, 5), 0.2).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_LINEAR).set_delay(0.2)
	tween_scale.tween_callback(func() -> void:
		lerp_speed = INITIAL_LERP_SPEED	
	)
	tween_scale.tween_property(self, "scale", Vector2(1, 1), 2).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_ELASTIC)
	
	toggle_outline(true)


func toggle_outline(toggle: bool) -> void:
	if toggle:
		material = outline_shader
	else:
		material = null


