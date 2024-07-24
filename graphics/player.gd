extends Node2D
class_name Player

	# "position": GamePosition,
	# "direction": string, // see below
	# "team": string,
	# "action": string or object, // see below
	# "inventory": [GameCellContent],
	# "state": string or object, // see below
	# "level": number,
	
@onready var animations: AnimatedSprite2D = $AnimatedSprite2D
@onready var action_label: RichTextLabel = %ActionLabel
@onready var polygon_2d: Polygon2D = %Polygon2D

var id: int = 0

const INITIAL_LERP_SPEED: float = 3
var lerp_speed: float = INITIAL_LERP_SPEED

var destination: Vector2

const Direction: Dictionary = {
	"North": "North",
	"South": "South",
	"East": "East",
	"West": "West"
}

const Action: Dictionary = {
	"Avance": "aod"
}

var map_pos: Vector2i
@onready var direction: String
				
var team: String
var inventory: Array
var level: int
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
			animations.play(WalkAnim.UP as StringName)
		"South":
			animations.play(WalkAnim.DOWN as StringName)
		"East":
			animations.play(WalkAnim.RIGHT as StringName)
		"West":
			animations.play(WalkAnim.LEFT as StringName)

func update_action_label() -> void:
	action_label.text = "[center]" + action + "[/center]"
	
func update_level_color() -> void:
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
	elif WalkAnimArray.has(animations.animation):
		animations.stop()
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

	
