# main.py
from game.rating import record_game, get_stats, get_recent_games

# Simulate a few games
print("Simulating games...\n")
record_game("aggressive_easy", 1091, "aggressive", "win")
record_game("defensive_medium", 1124, "defensive", "loss")
record_game("positional_hard", 1232, "positional", "draw")
record_game("aggressive_hard", 1293, "aggressive", "win")

stats = get_stats()
print(f"Rating:       {stats['rating']}")
print(f"Games played: {stats['games_played']}")
print(f"Wins:         {stats['wins']}")
print(f"Losses:       {stats['losses']}")
print(f"Draws:        {stats['draws']}")
print(f"Win rate:     {stats['win_rate']}%")

print("\nRecent games:")
for game in get_recent_games():
    change = f"+{game['change']}" if game['change'] > 0 else str(game['change'])
    print(f"  vs {game['bot']:<25} {game['result']:<5} "
          f"{game['rating_before']} → {game['rating_after']} ({change})")