# Solution 06 — Safety, Red-Teaming & Continuous Evaluation 🧪

**[← Back to Challenge 6](../../challenges/challenge-06.md)** · [Home](../../README.md)

**Bonus / optional.** Make the CLM assistant **production-safe**: adversarially attack
the *same* agent you shipped, run safety evaluations, and gate releases on a combined
**quality + safety** check in CI.

## Expected end state

- [`src/red_team.py`](../../src/red_team.py) runs the **AI Red Teaming Agent** against
  the Intake & Drafting agent and writes a repeatable scorecard
  (`redteam_scorecard.json`) you can track over time.
- [`src/safety_eval.py`](../../src/safety_eval.py) runs safety evaluators; the gate
  `--gate 0.1` fails the build on unsafe output — the security counterpart to
  Challenge 3's quality gate.

## Key files

| Path | Role |
|------|------|
| [`src/red_team.py`](../../src/red_team.py) | Automated red-teaming (`--num-objectives`, `--strategies`) → `redteam_scorecard.json` |
| [`src/safety_eval.py`](../../src/safety_eval.py) | Safety evaluation + CLM guardrail gate (`--safety-evals`, `--gate`) |

## Run it

```bash
python src/red_team.py --num-objectives 2                 # writes redteam_scorecard.json
python src/red_team.py --strategies --num-objectives 2    # add attack strategies
python src/safety_eval.py --safety-evals
python src/safety_eval.py --dry-run --gate 0.1            # gate for CI
```

> To **see the gate fail on purpose**, run `python src/safety_eval.py --dry-run --gate 0.0`.

## Common issues

| Symptom | Cause / fix |
|---------|-------------|
| Non-zero category in the scorecard | Tighten refusal/grounding instructions in [`src/agents/intake_drafting_agent.py`](../../src/agents/intake_drafting_agent.py). |
| Red-teaming agent unavailable | Confirm the AI Red Teaming Agent is enabled for your Foundry project/region. |
