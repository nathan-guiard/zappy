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

func animate() -> void:
	match direction:
		"North":
			animations.play("up_walk")
		"South":
			animations.play("down_walk")
		"East":
			animations.play("right_walk")
		"West":
			animations.play("left_walk")

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
