/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.rs                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/04 09:08:14 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/04 10:23:57 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use structopt::StructOpt;

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

fn main() {
    let mut args = Args::from_args();
    if args.team_name.is_empty() {
        args.team_name.push("Blue team".into());
    }

    dbg!(args);
}
