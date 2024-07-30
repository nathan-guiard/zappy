@tool
extends HBoxContainer
class_name ContentInfoRow


@onready var texture_rect: TextureRect = $MarginContainer/TextureRect
@onready var label_content_name: Label = $LabelContentName
@onready var label_amount: Label = $MarginContainer2/LabelAmount

@export var icon: Texture2D:
	set(val):
		icon = val
		texture_rect.texture = icon
		
@export var key: String:
	set(val):
		key = val
		label_content_name.text = key
		
@export var value: String:
	set(val):
		value = val
		label_amount.text = value
