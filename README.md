# Orbit Wars Agent
A competitive game AI agent for the [Kaggle Orbit Wars](https://www.kaggle.com/competitions/orbit-wars) competition - a real-time strategy game where players capture planets orbiting a sun in continuous 2D space.
**Competition:** 2,174 teams | \,000 prize pool
---
## Problem
Players start with one planet and must capture neutral and enemy planets by sending fleets. The core challenge: planets **orbit the sun**, so a naive agent that aims at the current planet position will always miss - the planet will have moved by the time the fleet arrives.
## Key Algorithm: Iterative Intercept Prediction
The main insight is treating fleet targeting as an **intercept problem**, not a pursuit problem.
### Naive approach (fails):
`python
# Aim at where the planet IS now
target_x, target_y = planet.current_x, planet.current_y
`
### Correct approach:
`python
def predict_intercept(src_x, src_y, target, step, initial_planets, angular_velocity, n_ships):
    # Start with current planet position
    t_estimate = travel_time(src, current_planet_pos, n_ships)
    # Iterate until convergence
    for _ in range(15):
        future_pos = get_planet_position(target, step + t_estimate)
        new_t = travel_time(src, future_pos, n_ships)
        if abs(new_t - t_estimate) <= 1:
            break
        t_estimate = new_t
    return future_pos  # where to aim
`
This converges in 3-5 iterations and solves the circular dependency between travel time and target position.
## Other Features
- **Fleet speed model** - speed scales logarithmically with fleet size (1 ship = 1 unit/turn, max 6)
- **Sun avoidance** - detects and reroutes fleets that would cross the sun
- **Continuous collision detection** - matches the game engine's segment-based collision (not point-based)
- **Greedy expansion** - scores targets by production * turns_remaining / (cost + distance)
- **Defense** - intercepts incoming enemy fleets before they reach owned planets
## Tech Stack
- Python 3.12
- [kaggle-environments](https://github.com/Kaggle/kaggle-environments)
## Usage
`bash
# Install dependencies
pip install kaggle-environments
# Test agent locally
python test.py
# Submit to Kaggle
python submit.py
`
## Project Structure
`
orbit-wars-agent/
??? agent.py      # Main agent logic
??? main.py       # Submission entry point
??? test.py       # Local testing vs random agent
??? submit.py     # Kaggle submission script
`
## What I Learned
- Game AI requires **predicting future state**, not reacting to current state
- Iterative numerical methods (intercept prediction) are more robust than closed-form solutions for moving targets
- Reading the game engine source code is essential - documentation alone is insufficient
- Elo-based leaderboards require many games to calibrate; local win rate vs random agent is a better short-term metric