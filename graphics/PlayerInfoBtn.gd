@tool
extends Button
class_name PlayerInfoBtn


@onready var texture_rect: TextureRect = $HBoxContainer/MarginContainer/TextureRect
@onready var label_info: Label = $HBoxContainer/LabeInfo

@export var logo: Texture2D:
	set(val):
		logo = val
		texture_rect.texture = logo
		
@export var info: String:
	set(val):
		info = val
		label_info.text = info


