/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   mod.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/05 17:25:42 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/15 09:43:22 by nguiard          ###   ########.fr       */
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
	pub graphic_interface: Option<GraphicClient>
}

impl Game {
	pub fn new(x: u8, y: u8, teams: u8, seed: usize) -> Self {
		let map = GameMap::new(x, y, teams, seed);
		Game {
			players: vec![],
			map: map.clone(),
			last_map: map.clone(),
			graphic_interface: None,
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
}