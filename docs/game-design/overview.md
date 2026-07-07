# Game Design Overview

## Core Concept

Secret Signal is a real-time multiplayer social deduction game where one player is secretly the Coordinator and must influence others to complete secret missions without being detected.

## Player Roles

### Coordinator
- Receives secret missions each round
- Must influence other players to complete missions through conversation
- Wins by completing missions and avoiding detection

### Detective
- Observes player behavior to identify the Coordinator
- May have limited investigation abilities (future implementation)

### Citizens
- Have personal objectives to create noise and make identification harder
- Help identify the Coordinator through observation

## Game Flow

Each round consists of:
1. Public Prompt - Creates natural conversation
2. Private Objectives - Coordinator gets mission, others get personal objectives
3. Interaction Phase - Players communicate via text, replies, reactions
4. Mission Evaluation - Backend determines if Coordinator's mission succeeded
5. Discussion Phase - Players discuss suspicions
6. Voting/Accusation - Players vote on suspected Coordinator
7. Round Result - Points awarded, progression to next round or game end

## Win Conditions

- Coordinator side scores points for completed missions, incorrect accusations, surviving rounds
- Investor side (Detective + Citizens) scores points for failed missions, correct accusations
- Team with highest score after all rounds wins