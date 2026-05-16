# rubiks

A little obsession of mine: I solved a physical Rubik's cube over a couple of months using my own (very inefficient) algorithms. This project is an attempt to do the same thing but much faster with an IDA\* search informed by a corner pattern database. I'm also using it as an excuse to lean on Claude to scaffold the skeleton so I can focus on implementation and pick up a few best practices along the way.

## Planned features

- **IDA\* search** with a corner pattern database heuristic to find near-optimal solutions quickly.
- **My own (slow) algorithm** ported into the same interface, so I can benchmark just how much slower a hand-rolled approach is against a real search.
- **Long term:** point a camera at a real cube and have it return a solution, computer-vision scan of the 6 faces, then run the solver and print the moves.

## Setup

```bash
uv sync
```
