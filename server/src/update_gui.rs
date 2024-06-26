/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   update_gui.rs                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/15 12:07:50 by nguiard           #+#    #+#             */
/*   Updated: 2024/06/03 12:39:04 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use serde::Serialize;

use crate::{communication::send_to, game::{egg::Egg, map::SendCell, player::SendPlayer, Game}};

pub fn update_gui(game: &Game) {
	if game.gui.is_none() {
		return;
	}
	let gui = game.gui.as_ref().unwrap();
	if !gui.enabled {
		return;
	}
	if game.last_map.is_none() {
		game.map.send_map(gui.fd)
	}
	
	let mut to_send = UpdateMap::new();
	
	for x in 0..game.map.max_position.x {
		for y in 0..game.map.max_position.y {
			let last_cell = &game.last_map.as_ref().unwrap().get_cell(x, y).unwrap();
			let new_cell = &game.map.get_cell(x, y).unwrap();
			if let Some(updated) = last_cell.diff_content(new_cell) {
				to_send.cells.push(updated);
			}
		}
	}

	for p in &game.players {
		if !p.team.is_empty() {
			to_send.players.push(SendPlayer::from(p.clone()))
		}
	}

	to_send.eggs = game.eggs.clone();

	let splitted = (serde_json::to_string(&to_send).unwrap() + "\x04")
								.chars()
								.collect::<Vec<char>>()
								.chunks(4096)
								.map(|c| c.iter().collect::<String>())
								.collect::<Vec<String>>();

	for chunk in splitted {
		send_to(gui.fd, chunk.as_str());
	}
}

#[derive(Serialize)]
struct UpdateMap {
	cells: Vec<SendCell>,
	players: Vec<SendPlayer>,
	eggs: Vec<Egg>,
}

impl UpdateMap {
	pub fn new() -> Self {
		Self {
			cells: vec![],
			players: vec![],
			eggs: vec![],
		}
	}
}