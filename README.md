# hanabi-bot

My project for the Computational Intelligence exam (Simone Sasso, 292608).

I decided to go for a rule based approach, since it seemed like the best performing option.

## How to run
The bot is inside `client.py`. You can decide to play for N matches by setting `INFINITE_PLAY = True`, otherwise the bot will stop after one match.

## Quick explanation
The rules are documented inside `rule_based.py`. I implemented some basic rules for the 2 players game, then I also tried some advanced strategies, like finesse and bluff, for the 3+ players matches.

Each player knows the current information every player has about his cards by using the `players_hints` dictionary, where the keys are the players names, and the values are a list of `MyCard` objects for each player. `MyCard` contains the current information I have about a card from the hint of other players, and also a table containing all the possibilities for that card, calculated by looking at the environment and excluding the cards present in other players hands, played on the table or discarded.

## Experimental results
Avg scores over 1000 matches (bot playing with other instances of itself)
* 2 players: 19.34
* 3 players: 19.65
* 4 players: 19.23
* 5 players: 18.48

## Credits
I worked in collaboration with Alessandro Speciale, sharing some ideas on the strategies, but each one developed its own bot.
