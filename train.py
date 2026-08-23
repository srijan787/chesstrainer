# train.py
# Run this ONCE to evolve the three bot style weight vectors.
# Takes ~5-10 minutes depending on your machine.
# Results saved to data/weights/

from ai.genetic import train_all_styles

if __name__ == "__main__":
    train_all_styles(
        generations=15,
        population_size=12
    )