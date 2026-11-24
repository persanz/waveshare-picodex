# Pikachu animation source

- Source: [PokeAPI/sprites, generation V Black/White animated Pikachu](https://github.com/PokeAPI/sprites/blob/master/sprites/pokemon/versions/generation-v/black-white/animated/25.gif)
- Git blob SHA: `904707ef456bf6d2409bdf2f7e834dae4a8a04d5`
- Original GIF retained unchanged as `pikachu.gif` (23,958 bytes, 50 × 46 pixels, 58 frames).
- Pokémon sprites and characters belong to their respective owners. This is an experimental display asset, not original artwork created for this project.

`build_pikachu_animation.py` composites transparency onto black and converts frames
to big-endian RGB565 with horizontal 3× nearest-neighbour scaling and
independent raw-DEFLATE compression (512-byte window). Source frame delays are retained (100/200 ms). On the board,
each row is repeated vertically 3× into the existing framebuffer. A single
300-byte row buffer and a small native decoder window are used; the compiled player and interpreter also consume
heap. This produces a 150 × 138 pixel sprite without scaling pixels in Python.
