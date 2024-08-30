@tool

extends Label
class_name TeamName

@export var title: String:
	set(new_val):
		title = new_val
		text = title
@export var color: Color:
	set(new_val):
		color = new_val
		modulate = color


