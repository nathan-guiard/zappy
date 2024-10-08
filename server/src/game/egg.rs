/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   egg.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/22 09:50:38 by nguiard           #+#    #+#             */
/*   Updated: 2024/08/16 15:12:09 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use serde::Serialize;

use super::map::GamePosition;

const TIME_TO_HATCH: u16 = 600;

#[derive(Debug, Serialize, Clone)]
pub struct Egg {
	position: GamePosition,
	team: String,
	timer: u16,
	id: u128,
}

impl Egg {
	pub fn new(position: GamePosition, team: String, id: u128) -> Self {
		Egg {
			position,
			team,
			timer: 0,
			id,
		}
	}

	pub fn try_hatch(&mut self) -> Option<(GamePosition, String)> {
		if self.timer == TIME_TO_HATCH {
			return Some((self.position, self.team.clone()));
		}
		self.timer += 1;
		println!("Egg hatching: {}/{TIME_TO_HATCH}", self.timer);
		None
	}
}