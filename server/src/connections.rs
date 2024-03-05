/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   connections.rs                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/04 14:12:44 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/05 12:21:25 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use std::io::Error;

use epoll::Events;
use libc::*;

use crate::watcher::Watcher;

#[derive(Clone, Copy)]
pub struct ServerConnection {
	soc_addr: sockaddr_in,
	pub socket_fd: i32,
}

pub fn init_socket(port: u16) -> ServerConnection {
	let mut result: ServerConnection;
	result = unsafe { std::mem::zeroed() };
	result.socket_fd = unsafe { socket(AF_INET, SOCK_STREAM, 0) };
	if result.socket_fd < 0 {
		// Return some kind of error
		todo!();
	}

	result.soc_addr.sin_addr.s_addr = INADDR_ANY.to_be();
	result.soc_addr.sin_port = port.to_be();
	result.soc_addr.sin_family = AF_INET as u16;

	if unsafe { fcntl(result.socket_fd, F_SETFL, O_NONBLOCK) }	< 0 {
		unsafe { libc::close(result.socket_fd) };
		// Return some kind of error;
		todo!();
	}

	if unsafe { bind(result.socket_fd,
		&result.soc_addr as *const _ as *const _,
		std::mem::size_of_val(&result.soc_addr) as u32) } != 0 {
		unsafe { libc::close(result.socket_fd) };
		// Return some kind of error
		todo!();
	}

	if unsafe { listen(result.socket_fd, 32) } != 0 {
		unsafe { libc::close(result.socket_fd) };
		// Return some kind of error
		todo!();
	}

	return result;
}

pub fn get_new_connections(con_data: &ServerConnection, watcher: &mut Watcher)
	-> Result<(), Error> {
	// Check for new connections (maybe another function)
	loop {
		let new_connection = unsafe {
			accept(con_data.socket_fd,
				std::ptr::null_mut(),
				std::ptr::null_mut())
		};
		if new_connection == -1 {
			let last_error = Error::last_os_error();
			if let Some(errno) = last_error.raw_os_error() {
				if errno == EWOULDBLOCK || errno == EAGAIN {
					println!("No (more) incoming connections");
					return Ok(());
				}
			}
			return Err(last_error);
		}
		println!("Connection!");
		watcher.add(new_connection, Events::EPOLLIN)?;
		todo!();
		return Ok(());
	}
}

fn get_data_single_client() {
	
}