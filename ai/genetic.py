# ai/genetic.py
# Genetic algorithm that evolves style-specific evaluation weight vectors
# Each "chromosome" is a dict of weights for the evaluation function
# The GA runs offline (before the app is used) and saves results to data/weights/

import random
import json
import os
import math
from engine.board import Board
from engine.moves import get_legal_moves
from engine.search import find_best_move, make_move
from engine.evaluation import evaluate

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(__file__))
WEIGHTS_DIR = os.path.join(BASE_DIR, "data", "weights")


# ── Chromosome structure ──────────────────────────────────────
# Each chromosome is a dict with 3 weights, all between 0.0 and 3.0
# material:  how much the bot values capturing/keeping pieces
# position:  how much the bot values piece placement
# mobility:  how much the bot values having active/mobile pieces

def random_chromosome():
    """Create a random weight vector."""
    return {
        "material": round(random.uniform(0.5, 3.0), 3),
        "position": round(random.uniform(0.5, 3.0), 3),
        "mobility": round(random.uniform(0.5, 3.0), 3),
    }


def crossover(parent_a: dict, parent_b: dict) -> dict:
    """
    Combine two parent chromosomes to produce a child.
    Each weight is randomly taken from either parent.
    """
    child = {}
    for key in parent_a:
        child[key] = parent_a[key] if random.random() < 0.5 else parent_b[key]
    return child


def mutate(chromosome: dict, rate: float = 0.2, strength: float = 0.3) -> dict:
    """
    Randomly adjust weights with probability = rate.
    strength controls how much each weight can change.
    """
    mutated = {}
    for key, value in chromosome.items():
        if random.random() < rate:
            delta = random.uniform(-strength, strength)
            mutated[key] = round(max(0.1, min(3.0, value + delta)), 3)
        else:
            mutated[key] = value
    return mutated


# ── Game simulation ───────────────────────────────────────────

def play_game(weights_white: dict, weights_black: dict,
              depth: int = 1, max_moves: int = 60) -> str:
    """
    Play a full game between two weight configurations.
    Returns 'white', 'black', or 'draw'.
    depth=1 keeps training fast enough to run in reasonable time.
    """
    board = Board()
    for move_num in range(max_moves):
        legal = get_legal_moves(board)
        if not legal:
            # No legal moves = checkmate or stalemate
            if move_num % 2 == 0:
                return "black"   # White had no moves
            else:
                return "white"   # Black had no moves

        weights = weights_white if board.turn == "white" else weights_black
        move    = find_best_move(board, depth=depth, weights=weights)
        if move is None:
            break
        make_move(board, move)

    # Game reached move limit — evaluate final position
    score = evaluate(board)
    if score > 50:
        return "white"
    elif score < -50:
        return "black"
    return "draw"


# ── Fitness functions (one per style) ────────────────────────

def fitness_aggressive(chromosome: dict, opponents: list,
                       depth: int = 1) -> float:
    """
    Aggressive style fitness:
    Rewards winning quickly and having high material + mobility weights.
    Penalises passive (low material) weight vectors.
    """
    wins = 0
    games = 0
    for opp in opponents:
        result = play_game(chromosome, opp, depth=depth)
        if result == "white":
            wins += 1
        games += 1
    win_rate = wins / games if games > 0 else 0

    # Style bias: reward high material and mobility weights
    style_bonus = (chromosome["material"] * 0.3 +
                   chromosome["mobility"] * 0.2)
    return win_rate + style_bonus * 0.2


def fitness_defensive(chromosome: dict, opponents: list,
                      depth: int = 1) -> float:
    """
    Defensive style fitness:
    Rewards not losing (draws count as partial wins).
    Rewards high positional weight.
    """
    score = 0
    games = 0
    for opp in opponents:
        result = play_game(chromosome, opp, depth=depth)
        if result == "white":
            score += 1.0
        elif result == "draw":
            score += 0.5   # draws are valued
        games += 1
    survival_rate = score / games if games > 0 else 0

    # Style bias: reward high positional weight
    style_bonus = chromosome["position"] * 0.3
    return survival_rate + style_bonus * 0.2


def fitness_positional(chromosome: dict, opponents: list,
                       depth: int = 1) -> float:
    """
    Positional style fitness:
    Rewards winning AND having balanced, high positional weight.
    """
    wins = 0
    games = 0
    for opp in opponents:
        result = play_game(chromosome, opp, depth=depth)
        if result == "white":
            wins += 1
        games += 1
    win_rate = wins / games if games > 0 else 0

    # Style bias: reward high position, penalise extreme material bias
    style_bonus = (chromosome["position"] * 0.4 -
                   abs(chromosome["material"] - 1.0) * 0.1)
    return win_rate + style_bonus * 0.2


# ── Core GA loop ──────────────────────────────────────────────

def run_ga(style: str, generations: int = 20,
           population_size: int = 16, depth: int = 1):
    """
    Run the genetic algorithm for a given style.

    style:           'aggressive', 'defensive', or 'positional'
    generations:     how many generations to evolve
    population_size: number of chromosomes per generation
    depth:           minimax depth used during training games
                     (keep at 1 for reasonable training speed)

    Saves the best chromosome to data/weights/<style>.json
    """
    fitness_fn = {
        "aggressive": fitness_aggressive,
        "defensive":  fitness_defensive,
        "positional": fitness_positional,
    }[style]

    print(f"\n=== GA Training: {style.upper()} style ===")
    print(f"Population: {population_size}  |  "
          f"Generations: {generations}  |  Depth: {depth}\n")

    # Initialise random population
    population = [random_chromosome() for _ in range(population_size)]

    best_ever        = None
    best_ever_score  = -math.inf

    for gen in range(generations):
        # ── Evaluate fitness ─────────────────────────────────
        # Each chromosome plays against 4 random opponents
        # from the current population
        scored = []
        for i, chrom in enumerate(population):
            opponents = random.sample(
                [p for j, p in enumerate(population) if j != i],
                min(4, population_size - 1)
            )
            score = fitness_fn(chrom, opponents, depth=depth)
            scored.append((score, chrom))

        # Sort best first
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score  = scored[0][0]
        best_chrom  = scored[0][1]

        if best_score > best_ever_score:
            best_ever_score = best_score
            best_ever       = best_chrom.copy()

        print(f"Gen {gen + 1:02d}/{generations}  |  "
              f"Best fitness: {best_score:.4f}  |  "
              f"Weights: {best_chrom}")

        # ── Selection: keep top 50% ──────────────────────────
        survivors = [chrom for _, chrom in
                     scored[:population_size // 2]]

        # ── Reproduction: fill back to population_size ───────
        new_population = survivors.copy()
        while len(new_population) < population_size:
            parent_a = random.choice(survivors)
            parent_b = random.choice(survivors)
            child    = crossover(parent_a, parent_b)
            child    = mutate(child)
            new_population.append(child)

        population = new_population

    # ── Save best result ──────────────────────────────────────
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    out_path = os.path.join(WEIGHTS_DIR, f"{style}.json")
    with open(out_path, "w") as f:
        json.dump({
            "style":   style,
            "weights": best_ever,
            "fitness": round(best_ever_score, 4),
        }, f, indent=2)

    print(f"\nBest weights saved → {out_path}")
    print(f"Final weights: {best_ever}")
    return best_ever


def train_all_styles(generations: int = 20,
                     population_size: int = 16):
    """Train all three styles and save their weights."""
    results = {}
    for style in ["aggressive", "defensive", "positional"]:
        weights = run_ga(style,
                         generations=generations,
                         population_size=population_size)
        results[style] = weights
    print("\n=== All styles trained successfully ===")
    for style, w in results.items():
        print(f"{style:12s}: {w}")
    return results