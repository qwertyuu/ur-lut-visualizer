## About

This interactive explorer lets you dive deep into the Royal Game of Ur's strategic possibilities through a comprehensive lookup table (LUT), which the original files can be found [here](https://huggingface.co/sothatsit/RoyalUrModels). 

For now, only the finkel.rgu file is supported, meaning that only finkel rulesets and "standard" rules apply (4 dice, 7 pawns, 2 players, safe rosettes that give a re-roll when you enter them, no stacking and "standard" route for each player with no overlap at the bottom of the map). 

While designed for intermediate to advanced players, it offers intuitive insights into winning probabilities for any given board state.

## Key Features

- **Real-time Win Probability**: For every board position, see the exact winning chances for both players (○ for light and ● for dark)
- **Move Analysis**: Explore how each possible move affects your winning probability
- **State Editor**: Customize board positions to analyze specific scenarios
- **Visual Board Layout**: ASCII representation of the classic Royal Game of Ur board, including:
  - Rosette squares (☆)
  - Player pieces (○ for light and ● for dark)

## Why Use This Tool?

Perfect for:
- Analyzing difficult positions
- Understanding subtle strategic choices
- Improving your decision-making through probability analysis
- Studying specific board states that arise in your games

## How to Use

1. **Start Position**: Begin with a fresh game or use the State Editor to set up a specific position and pick the current player
2. **Available Moves**: For each possible dice roll (0-4), see:
   - All legal moves
   - The resulting board position
   - How each move impacts your winning probability (shown as percentage changes)
3. **Strategic Analysis**: Use the probability changes to understand:
   - Which moves are optimal
   - How different board positions affect your chances of winning
   - The impact of landing on special squares

## Join the Community!

The Royal Game of Ur has a vibrant online community, and there are several ways to get involved:

### Open Source Development
This LUT explorer is open source and welcomes contributions! Whether you're a developer, designer, or enthusiast, you can help shape the future of this tool through our [GitHub repository](https://github.com/qwertyuu/ur-lut-visualizer).

### Community Platforms
- **Discord Community**: Join our [active Discord server](https://discord.gg/fyNjxBPCSz) to discuss strategies, share insights, and connect with fellow players
- **Online Gaming**: Experience the game on [royalur.net](https://royalur.net/), featuring:
  - Real-time matches against players worldwide
  - Post-game analysis tools
  - Active community discussions

### Alternative Variants
Explore different approaches to the game on [ur.whnet.ca](https://ur.whnet.ca/), offering:
- Unique variations with 3 or 5 pawns for quicker games
- Alternative AI implementations
- Different strategic challenges
_(Note: Interface is in French - translation tools recommended)_

Whether you're interested in developing tools, playing matches, or discussing strategy, there's a place for you in the Royal Game of Ur community!

## Credits

This tool stands on the shoulders of giants in the Royal Game of Ur community on Discord. Here are the key contributors who made this LUT explorer possible:

### Development & Implementation
- **Raphaël "Urph" Côté**
  - Web interface development (this website!)
  - Binary LUT file reader implementation
  - Interactive exploration system design and implementation

### Lookup Table Generation
- **Padraig "Paddy" Lamont**
  - Creation of comprehensive LUT files
  - State probability calculations
  - Core game state analysis

### Original Research
- **Jeroen (Jex248)**
  - Pioneered the LUT approach for the Royal Game of Ur
  - Developed the iterative state propagation methodology
  - Demonstrated the game's solvability through LUT analysis

This collaboration between researchers, developers, and game theorists has helped advance our understanding of this ancient game through modern computational methods.
