/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   mod.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/05 17:25:42 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/15 10:17:21 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

pub mod map;
pub mod player;
pub mod graphic_client;

use self::{map::GameMap, player::Player, graphic_client::GraphicClient};

const TURNS_TO_DIE: u16 = 150;

pub struct Game {
	pub players: Vec<Player>,
	pub map: GameMap,
	last_map: GameMap, // needed for updates to graphic interface
	pub graphic_interface: Option<GraphicClient>,
	pub teams: Vec<String>,
}

impl Game {
	pub fn new(x: u8, y: u8, teams: Vec<String>, seed: usize) -> Self {
		let map = GameMap::new(x, y, teams.len() as u8, seed);
		Game {
			players: vec![],
			map: map.clone(),
			last_map: map.clone(),
			graphic_interface: None,
			teams,
		}
	}
}

impl Game {
	pub fn try_remove_graphic_interface(&mut self, fd: i32) {
		match &self.graphic_interface {
			Some(gc) => if fd == gc.fd { self.graphic_interface = None },
			None => {},
		}
	}

	pub fn execute(&mut self) {
		let mut to_remove = None;
		let mut players_to_remove = Vec::new();
	
		for player in self.players.iter_mut() {
			if player.execute_queue(&self.map, &self.teams, self.graphic_interface.is_some()) {
				to_remove = Some(player.fd);
			}
		}
	
		if let Some(fd) = to_remove {
			players_to_remove.push(fd);
			self.players.retain(|p| players_to_remove.contains(&p.fd));
			self.graphic_interface = Some(GraphicClient::new(to_remove.unwrap()));
			self.map.send_map(self.graphic_interface.as_ref().unwrap().fd);
		}
	}
}