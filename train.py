# train.py
# Run this ONCE before launching the app.
# Step 1: evolves the three style weight vectors via GA
# Step 2: calibrates each bot's ELO via a tournament

from ai.genetic import train_all_styles
from ai.calibration import run_calibration

if __name__ == "__main__":
    print("Step 1: Training styles via genetic algorithm...")
    train_all_styles(generations=15, population_size=12)

    print("\nStep 2: Calibrating ELO ratings via tournament...")
    run_calibration(games_per_pair=2)

    print("\nAll done — app is ready to run.")