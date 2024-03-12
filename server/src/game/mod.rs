/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   mod.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/05 17:25:42 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/12 17:55:20 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

pub mod map;
pub mod player;

use self::{map::GameMap, player::Player};

const TURNS_TO_DIE: u16 = 150;

pub struct Game {
	pub players: Vec<Player>,
	pub map: GameMap,
	last_map: GameMap, // needed for updates to graphic obs
}

impl Game {
	pub fn new(x: u8, y: u8, teams: u8, seed: usize) -> Self {
		let map = GameMap::new(x, y, teams, seed);
		Game {
			players: vec![],
			map: map.clone(),
			last_map: map.clone(),
		}
	}
}