/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   gui.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/12 18:12:59 by nguiard           #+#    #+#             */
/*   Updated: 2024/04/08 10:44:06 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use crate::communication::send_to;

#[derive(Debug)]
pub struct GraphicClient {
	pub fd: i32,
	pub enabled: bool,
}

impl GraphicClient {
	pub fn new(fd: i32) -> Self {
		GraphicClient {
			fd,
			enabled: false,
		}
	}

	pub fn enable(&mut self, lines: Vec<String>) -> bool{
		for line in lines {
			if line.to_ascii_lowercase() == "ready\n" {
				self.enabled = true;
				return true;
			} else {
				send_to(self.fd, "The only way to enable the updates is to type 'ready\\n'.\n")
			}
		}
		false
	}
}