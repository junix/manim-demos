# Manim Demos

Twelve explanatory reference scenes where the transparent PNG is the primary deliverable and a short MP4 preserves the temporal argument.

`catalog.json` records the teaching use, question, temporal visual family, complexity, and tags.

| Search trace | Fourier | Geometry proof | Gradient descent |
|---|---|---|---|
| [![search](out/algorithm-trace-transparent.png)](out/algorithm-trace.mp4) | [![fourier](out/fourier-phasors-transparent.png)](out/fourier-phasors.mp4) | [![proof](out/geometric-proof-transparent.png)](out/geometric-proof.mp4) | [![gradient](out/gradient-descent-transparent.png)](out/gradient-descent.mp4) |
| Neural pass | Sorting network | State machine | Bayesian update |
| [![neural](out/neural-forward-pass-transparent.png)](out/neural-forward-pass.mp4) | [![sorting](out/sorting-network-transparent.png)](out/sorting-network.mp4) | [![states](out/protocol-state-machine-transparent.png)](out/protocol-state-machine.mp4) | [![bayes](out/bayesian-update-transparent.png)](out/bayesian-update.mp4) |
| Orbital transfer | Matrix transform | Queue flow | L-system |
| [![orbit](out/orbital-transfer-transparent.png)](out/orbital-transfer.mp4) | [![matrix](out/matrix-transform-transparent.png)](out/matrix-transform.mp4) | [![queue](out/queueing-flow-transparent.png)](out/queueing-flow.mp4) | [![growth](out/l-system-growth-transparent.png)](out/l-system-growth.mp4) |

```bash
uv sync
uv run python scripts/render.py
uv run ruff check .
uv run pytest
```

The renderer executes Manim twice per scene: a last-frame Cairo render with alpha, and a low-resolution explanatory video. PNGs are checked for real transparency and visual content; videos are checked with `ffprobe`.
