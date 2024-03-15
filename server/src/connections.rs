/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   connections.rs                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/04 14:12:44 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/12 18:28:02 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use std::io::Error;

use epoll::Events;
use libc::*;

use colored::Colorize;
use crate::{game::player::Player, watcher::Watcher};

#[derive(Clone, Copy)]
pub struct ServerConnection {
	soc_addr: sockaddr_in,
	pub socket_fd: i32,
}

impl ServerConnection {
	pub fn init_socket(port: u16) -> Result<ServerConnection, Error> {
		let mut result: ServerConnection;
		result = unsafe { std::mem::zeroed() };
		result.socket_fd = unsafe { socket(AF_INET, SOCK_STREAM, 0) };
		if result.socket_fd < 0 {
			eprintln!("{}", "Could not create a socket".red().bold());
			return Err(Error::last_os_error())
		}
	
		result.soc_addr.sin_addr.s_addr = INADDR_ANY.to_be();
		result.soc_addr.sin_port = port.to_be();
		result.soc_addr.sin_family = AF_INET as u16;
	
		if unsafe { fcntl(result.socket_fd, F_SETFL, O_NONBLOCK) }	< 0 {
			let error = Error::last_os_error();
			unsafe { libc::close(result.socket_fd) };
			eprintln!("{}", "Could not set socket fd to non-blocking".red().bold());
			return Err(error);
		}
	
		if unsafe { bind(result.socket_fd,
			&result.soc_addr as *const _ as *const _,
			std::mem::size_of_val(&result.soc_addr) as u32) } != 0 {
				let error = Error::last_os_error();
				unsafe { libc::close(result.socket_fd) };
				eprintln!("{} {port}", "Could not set socket to port".red().bold());
				eprintln!("{}", "Hint: Try another port".yellow());
				return Err(error);
		}
	
		if unsafe { listen(result.socket_fd, 32) } != 0 {
			let error = Error::last_os_error();
			unsafe { libc::close(result.socket_fd) };
			eprintln!("{}", "listen() failed".red().bold());
			return Err(error);
		}
	
		Ok(result)
	}
	
	pub fn get_new_connections(&self, watcher: &mut Watcher)
		-> Result<Option<Player>, Error> {
		let new_connection = unsafe {
			accept(self.socket_fd,
				std::ptr::null_mut(),
				std::ptr::null_mut())
		};
		if new_connection == -1 {
			let last_error = Error::last_os_error();
			if let Some(errno) = last_error.raw_os_error() {
				if errno == EWOULDBLOCK || errno == EAGAIN {
					return Ok(None);
				}
			}
			eprintln!("{}", "accept() failed".red().bold());
			return Err(last_error);
		}
		println!("Connection!");
		unsafe { fcntl(new_connection, F_SETFL, O_NONBLOCK) };
		watcher.add(new_connection, Events::EPOLLIN | Events::EPOLLRDHUP)?;
		unsafe { send(new_connection, "BIENVENUE\n".as_bytes().as_ptr() as _, 10, 0) };
		Ok(Some(Player::new(new_connection)))
	}

	// TODO: remove or change the Player with the associated FD
	pub fn deconnection(&self, fd: i32, watcher: &mut Watcher)
		-> Result<i32, Error> {
		println!("Deconnection!");
		watcher.delete(fd)?;
		epoll::close(fd)?;
		Ok(fd)
	}
}