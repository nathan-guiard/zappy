extends Area2D
class_name Player

	# "position": GamePosition,
	# "direction": string, // see below
	# "team": string,
	# "action": string or object, // see below
	# "inventory": [GameCellContent],
	# "state": string or object, // see below
	# "level": number,

const Direction: Dictionary = {
	"North": "North",
	"South": "South",
	"East": "East",
	"West": "West"
}

const Action: Dictionary = {
	"Avance": "aod"
}

#var position: Vector2i
var direction: String
#
#func move(direction: Vector2i) -> void:
	#position += direction
