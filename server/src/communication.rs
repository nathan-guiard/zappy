/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   communication.rs                                   :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/07 05:53:29 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/07 10:12:05 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use std::{collections::HashMap, io::Error};

use libc::{c_void, EWOULDBLOCK};

use crate::game::map::GameMap;

pub fn process_data(data: &HashMap<i32, Vec<String>>, game_map: &GameMap) {
	for (fd, lines) in data {
		for line in lines {
			if line.is_empty() {
				continue;
			}
			if line.to_lowercase().starts_with("map") {
				game_map.send_map(*fd);
			}
		}
	}
}

pub fn get_all_data(ready_to_read: &Vec<i32>)
	-> Result<HashMap<i32, Vec<String>>, Error> {
	let mut data: HashMap<i32, Vec<String>> = HashMap::new();

	for fd in ready_to_read {
		data.insert(*fd, get_data_from_fd(*fd)?);
	}

	Ok(data)
}

pub fn get_data_from_fd(fd: i32) -> Result<Vec<String>, Error> {
	let mut buf = [0_u8; 1024];
	let mut line = String::new();

	loop {
		match unsafe { libc::read(fd, buf.as_mut_ptr() as *mut c_void, 1024) } {
			0 => {
				break;
			}
			size => {
				if size == -1 {
					let last_error = Error::last_os_error();
					if let Some(e) = last_error.raw_os_error() {
						if e == EWOULDBLOCK {
							break;
						}
						return Err(last_error);
					}
				}
				line += String::from_utf8_lossy(&buf[0..size as usize]).to_string().as_str()
			}
		}
	}
	let lines: Vec<String> = line.split('\n').map(|l| l.to_string()).collect();
	Ok(lines)
}