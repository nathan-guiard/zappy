/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   mod.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/05 17:25:42 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/15 18:05:58 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

pub mod map;
pub mod player;
pub mod gui;

use self::{map::GameMap, player::Player, gui::GraphicClient};

const TURNS_TO_DIE: u16 = 150;

#[derive(Debug)]
pub struct Game {
	pub players: Vec<Player>,
	pub map: GameMap,
	pub last_map: Option<GameMap>, // needed for updates to gui
	pub gui: Option<GraphicClient>,
	pub teams: Vec<String>,
}

impl Game {
	pub fn new(x: u8, y: u8, teams: Vec<String>, seed: usize) -> Self {
		let map = GameMap::new(x, y, teams.len() as u8, seed);
		Game {
			players: vec![],
			map: map.clone(),
			last_map: None,
			gui: None,
			teams,
		}
	}
}

impl Game {
	pub fn try_remove_gui(&mut self, fd: i32) {
		match &self.gui {
			Some(gc) => if fd == gc.fd { self.gui = None },
			None => {},
		}
	}

	/// Logic of the game, what occurs every tick
	pub fn execute(&mut self) {
		let mut to_remove = None;
		let mut players_to_remove = Vec::new();
		
		for player in self.players.iter_mut() {
			player.execute_casting(&mut self.map);
			if player.execute_queue(&self.map, &self.teams, self.gui.is_some()) {
				to_remove = Some(player.fd);
			}
		}
		
		if let Some(fd) = to_remove {
			players_to_remove.push(fd);
			self.players.retain(|p| players_to_remove.contains(&p.fd));
			self.gui = Some(GraphicClient::new(to_remove.unwrap()));
			self.map.send_map(self.gui.as_ref().unwrap().fd);
		}
		
		for player in &mut self.players {
			player.loose_food();
			player.increment_casting();
		}
	}
}