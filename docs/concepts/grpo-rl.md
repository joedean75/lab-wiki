# Distillation, RL and GRPO

These are the reasoning-model techniques used in [Pipeline_claude](../projects/pipeline-claude.md) and
[Astra](../projects/astra.md).

## How it works

### Distillation

A large **teacher** model writes worked solutions ("reasoning traces"); a small **student** is
fine-tuned to reproduce them, answer included. Here the traces are DeepSeek-R1 maths solutions
(`deepseek-r1-math-train.json`). Distillation turns a base model into one that "thinks before
answering". Supervise only the response tokens; long traces need a high length cap (≥ 2,048), or the
filter drops nearly everything.

### Reinforcement learning with verifiable rewards (RLVR)

Instead of copying a teacher, let the model try, and **reward** it when a checker says the final
answer is right (maths answer equals the key). No reward model needed — the verifier is the reward.

### GRPO (Group Relative Policy Optimization)

For each problem, sample a **group** of answers (e.g. 4–8). Score each. A completion's **advantage**
is its reward minus the group's mean (often divided by the group's spread). Increase the probability
of above-average completions and decrease below-average ones.

- No separate value network (cheaper than PPO).
- **If every answer in a group gets the same reward, the advantage is zero and the group teaches
  nothing.** Problems that are always solved or never solved waste compute — hence the
  **difficulty filter**: train on the "learnable band" (solved sometimes).
- A **KL penalty** to a frozen reference model keeps the policy from drifting into gibberish; PPO-style
  **clipping** limits each update.
- A **format reward** (e.g. for using `\boxed{}`) helps only if it varies inside a group; saturated, it
  is a constant that cancels out of the advantage.

### What the experiments showed

| Round | Result | Why |
|---|---|---|
| GRPO round 1 | **37.6 % → 48.1 %** MATH500 (+10.5, p < 0.001), answers 2.5× shorter | The 640-token rollout cap paid reward only for concluding in budget: **implicit brevity pressure** fixed the base's rambling. |
| GRPO round 2 | **54.0 % → 44.7 %** (−9.3, p < 0.05) | The model was already concise, so no general behaviour was left to shape; 72 updates over 16–19 filtered problems just **overfit**. |

Lesson: a narrow difficulty filter is powerful when a *global* behaviour needs fixing and destructive
once only problem-specific gradient is left.

### Inference-time scaling

Without training: sample *k* answers and **majority-vote** (self-consistency) — typically +5–15 points
on maths. `pass@k` (any of *k* right) is an oracle ceiling, useful as a diagnostic only.
