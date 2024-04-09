# Communication with the server

## What sends what

### Graphical user interface

On connection, the server sends the whole map as it is. <br />
It sends an array of an array of cells, so `[[SendCell]]`

Then, the gui has to send `ready\n` to recieve the updates.

If ready, on every tick, the server sends the updated cells and every player
(because every player HAS TO be update due to food loss). <br />
It sends an `UpdateMap`.

### AI Client

On connection, the server sends `BIENVENUE\n` then expects a team name. When a viable team name is given, the server sends the number of available connections and the size of the map like this: `<connections>\n<X> <Y>\n`.<br />
If `<connections>` is more than 0, the client can send commands to the server. Otherwise the client can retry later to input a team name. 

Data types sent in response of the commands:
- avance: ok/ko
- gauche: ok/ko
- droite: ok/ko
- prend: ok/ko
- pose: ok/ko
- expulse: ok/ko
- broadcast: ok
- incantation: ok/ko
- connect: number
- fork: ok/ko
- voir: `[SendCell]`
- inventaire: `[GameCellContent]`

### Special events

When player sends a broadcast, every other players will recieve:
- `broadcast <x>: <message>`

Where `<x>` is a digit and `<mesage>` is the message of the player. <br />
`<x>` is a digit to localise where the message has been sent from, as written in the 6th page of the project

When a player is kicked from its cell, the server sends `deplacement <direction>\n` where `<direction>` is either North, South, East or West.<br />
When a player reiceves this data, it has been moved and its ongoing casting is interrupted.

When the player dies, the server sends `You died\n` and disconnects the player.

When the game ends, the server sends `End of game: <reason>\n`.

When a client is disconnected, the server sends `Disconnected from the server: server closed\n` beforehand

## Data types

### UpdateMap

```json
{
	"cells": [SendCell],
	"players": [SendPlayer],
	"eggs": [Egg]
}
```

---
### SendCell:

```json
{
	"p": GamePosition,
	"c": [GameCellContent], 
}
```

---
### GamePosition

```json
{
	"x": number,
	"y": number, 
}
```

---
### GameCellContent

```json
{
	"Linemate": number, // OR
	"Deraumere": number, // OR
	"Sibur": number, // OR
	"Mendiane": number, // OR
	"Phiras": number, // OR
	"Thystame": number, // OR
	"Player": number, // OR
	"Food": number, // OR
	"Egg":  number,
}
```

---
### SendPlayer

```json
{
	"position": GamePosition,
	"direction": string, // see below
	"team": string,
	"action": string or object, // see below
	"inventory": [GameCellContent],
	"state": string or object, // see below
	"level": number,
}
```

direction can only be one of:
- `North`
- `South`
- `East`
- `West`

action can only be one of:
- `"Avance"`
- `"Gauche"`
- `"Droite"`
- `"Voir"`
- `"Inventaire"`
- `"Expulse"`
- `"Incantation"`
- `"Fork"`
- `"Connect"`
- `"NoAction"`
- `"Prend": string`
  - The string is what is being taken
- `"Pose": string`
  - The string is what is being dropped
- `"Broadcast": string`
  - The string is what will be braodcasted

state can only be one of:
- `"Idle"`
- `"Levelmax"`
- `"Dead"`
- `"Casting": [number, number]`
  - The first number is the current progress
  - The second number is the amount of steps needed

---
### Egg
```json
{
	"position": GamePosition,
	"team": string,
	"timer": number,
}