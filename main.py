# main.py
from game.rating import get_rating
from game.ladder import (get_ladder_progress, get_next_rung,
                         check_and_award)

rating   = get_rating()
progress = get_ladder_progress(rating)
next_rung = get_next_rung(rating)

print(f"Player rating: {rating}")
print(f"Ladder progress: {progress['completed']}/{progress['total']} completed")
print(f"Available: {progress['available']}  Locked: {progress['locked']}\n")

if next_rung:
    print(f"Next challenge: Rung {next_rung['rung']} — {next_rung['label']}")
    print(f"  Bot:   {next_rung['bot']} ({next_rung['bot_elo']} ELO)")
    print(f"  Style: {next_rung['style']}")
    print(f"  {next_rung['description']}\n")

# Simulate winning rung 1
reward = check_and_award("aggressive_easy", "win", rating)
if reward:
    print(f"Reward: {reward}")

progress = get_ladder_progress(rating)
print(f"Progress after win: {progress['completed']}/{progress['total']}")