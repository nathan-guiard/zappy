/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.rs                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/04 09:08:14 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/05 13:09:09 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

mod connections;
mod watcher;

use std::time::Duration;
use epoll::Events;
use libc::EPOLLIN;
use structopt::StructOpt;

use connections::{get_new_connections, init_socket};
use watcher::Watcher;

#[derive(StructOpt, Debug)]
struct Args {
    #[structopt(short, long, default_value = "4227")]
    port: u16,

    /// The map width
    #[structopt(short, default_value = "180")]
    x: u16,

    /// The map height
    #[structopt(short, default_value = "100")]
    y: u16,

    /// The team name(s)
    #[structopt(short = "n", long)]
    team_name: Vec<String>,

    /// The number of clients authorized at the beginning of the game
    #[structopt(short, long, default_value = "100")]
    clients: u8,

    /// The time unit divider, every step of the server will go at 1/t second
    #[structopt(short, long, default_value = "16")]
    time: u8,
}

fn main() -> Result<(), std::io::Error> {
    let mut args = Args::from_args();
    if args.team_name.is_empty() {
        args.team_name.push("Blue team".into());
    }
	let tick_speed = Duration::from_secs_f64(1 as f64 / args.time as f64);

	let con_data = init_socket(args.port);
	let mut watcher = Watcher::new()?;

	
	watcher.add(con_data.socket_fd, Events::EPOLLIN)?;

	loop {
		let new_events = match watcher.update() {
			Ok(events) => events,
			Err(e) => {
				eprintln!("Error trying to update: {e}");
				return Err(e);
			}
		};

		if new_events.len() == 0 {
			println!("No new events");
		}

		for event in new_events {
			if event.data == con_data.socket_fd as u64 &&
				event.events == EPOLLIN as u32 {
				get_new_connections(&con_data, &mut watcher)?;
			} else {
				todo!();
			}
		}

		// END OF LOOP
		std::thread::sleep(tick_speed);
	}
}