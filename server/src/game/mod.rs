/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   mod.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/05 17:25:42 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/19 11:09:18 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

pub mod map;
pub mod player;
pub mod gui;

use crate::communication::send_to;

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
		
		for player in self.players.iter_mut() {
			player.execute_casting(&mut self.map);
			if player.execute_queue(&self.map, &self.teams, self.gui.is_some()) {
				to_remove = Some(player.fd);
			}
		}
		
		if let Some(fd) = to_remove {
			self.players.retain(|p| p.fd == fd);
			self.gui = Some(GraphicClient::new(to_remove.unwrap()));
			self.map.send_map(self.gui.as_ref().unwrap().fd);
		}
		
		for player in &mut self.players {
			player.loose_food();
			player.increment_casting();
		}
	}
}

impl Drop for Game {
	fn drop(&mut self) {
		for x in &self.players {
			send_to(x.fd, "Disconnected from the server: server closed\n");
			unsafe { libc::close(x.fd) };
		}
	}
}