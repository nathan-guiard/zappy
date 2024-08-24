extends Node2D
class_name TraceSquare


var overlaps_count: int = 0:
	set(value):
		if value != overlaps_count:
			overlaps_count = value
			modulate = colors[clampi(overlaps_count, 0, colors.size() - 1)]

var colors: Array[Color] = [
	#Color("#000000", 1),
	Color("#FFffFF", 0.6),
	#Color("#fffad9", 0.6),
	Color("#fff4b1", 0.6), #jaune
	#Color("#ffef8d", 0.6),
	Color("#ffeb69", 0.6),
	#Color("#fde550", 0.6),
	Color("#ffe540", 0.6),
	#Color("#ffe22c", 0.6),
	Color("#fedf1e", 0.6),
	#Color("#ffde0c", 0.6),
	Color("#ffdc00", 0.6),
	#Color("#ffc45a", 0.6), #orange
	Color("#ffbb42", 0.6),
	#Color("#feb738", 0.6),
	Color("#ffb329", 0.6),
	#Color("#ffaf20", 0.6),
	Color("#ffab14", 0.6),
	#Color("#ffa80b", 0.6),
	Color("#ffa400", 0.6),
	Color("#ff8531", 0.6), #orange-rouge
	Color("#ff7e25", 0.6),
	Color("#ff7414", 0.6),
	Color("#ff6e09", 0.6),
	Color("#ff6800", 0.6),
	Color("#ff6029", 0.6), #rouge
	Color("#ff561b", 0.6),
	Color("#ff4e10", 0.6),
	Color("#ff4200", 0.6),
	Color("#ff2929", 0.6), #rouge-rouge
	Color("#ff1b1b", 0.6),
	Color("#ff1111", 0.6),
	Color("#ff0000", 0.6),
]

func _ready() -> void:
	modulate = colors[clampi(overlaps_count, 0, colors.size() - 1)]
	
