/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   watcher.rs                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/05 10:00:27 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/05 12:15:02 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use std::{io::Error, os::fd::RawFd};

use epoll::{ControlOptions::*, Event, Events};

#[derive(Debug)]
pub struct Watcher {
	epoll_fd: RawFd,
	watched: usize,
}

impl Drop for Watcher {
	fn drop(&mut self) {
		if let Err(e) = epoll::close(self.epoll_fd) {
			eprintln!("Could not close {}: {e}", self.epoll_fd);
		}
	}
}

impl Watcher {
	pub fn add(&mut self, fd: i32, events: Events) -> Result<(), Error> {
		let event = Event::new(events, fd as u64);
		epoll::ctl(self.epoll_fd, EPOLL_CTL_ADD, fd, event)?;
		self.watched += 1;
		Ok(())
	}

	pub fn delete(&mut self, fd: i32) -> Result<(), Error>{
		let event = Event::new(Events::empty(), fd as u64);
		epoll::ctl(self.epoll_fd, EPOLL_CTL_DEL, fd, event)?;
		self.watched -= 1;
		Ok(())
	}

	pub fn update(&self) -> Result<Vec<epoll::Event>, Error> {
		if self.watched == 0 {
			return Ok(Vec::new());
		}
		let mut events: Vec<Event> = Vec::with_capacity(self.watched);
		epoll::wait(self.epoll_fd, 0, &mut events)?;
		Ok(events)
	}

	pub fn new() -> Result<Self, Error> {
		Ok(Watcher {
			epoll_fd: epoll::create(false)?,
			watched: 0,
		})
	}
}