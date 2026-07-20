#!/usr/bin/env python3
"""Render the Contoso Global user-journey diagram.

Draws the contract manager's end-to-end day with the Agentic CLM assistant:
the six steps from the top-level README's "end-to-end journey" table, each
mapped to the agent / model that powers it, the Foundry capability, and the
challenge where it is built.

Colours follow the canonical architecture legend
(``docs/diagrams/architecture.svg``): blue = GPT agents, purple = Claude
agents, orange = Foundry IQ / tools, green = human sign-off, teal = the
proactive Teams alert back to the manager.

Outputs:
    docs/diagrams/user-journey.svg
    docs/diagrams/user-journey.png

Usage:
    python scripts/make_user_journey.py
"""
from __future__ import annotations

import pathlib
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

# Emit SVG text as vector paths so the diagram renders identically on GitHub
# regardless of whether Segoe UI is installed on the viewer's machine.
plt.rcParams["svg.fonttype"] = "path"

# --------------------------------------------------------------------------
# Fonts — prefer Segoe UI on Windows, fall back to the default sans stack.
# --------------------------------------------------------------------------
for _f in (
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\seguisb.ttf",
):
    try:
        fm.fontManager.addfont(_f)
    except Exception:  # noqa: BLE001 - font is optional
        pass
try:
    plt.rcParams["font.family"] = "Segoe UI"
except Exception:  # noqa: BLE001
    pass

# --------------------------------------------------------------------------
# Palette (matches docs/diagrams/architecture.svg legend)
# --------------------------------------------------------------------------
INK = "#1B1A19"
MUTED = "#5A5A66"
CARD_FILL = "#F7FAFD"
CARD_EDGE = "#D9E2EC"

GPT = "#0078D4"        # GPT agents (blue)
CLAUDE = "#7A4FB5"     # Claude / Anthropic agents (purple)
TOOLS = "#E8590C"      # Foundry IQ / tools (orange)
HITL = "#2F9E44"       # human sign-off (green)
TEAL = "#0C8599"       # proactive Teams alert / manager (teal)

PERSONA_FILL = "#E6F7F7"
FOOTER_FILL = "#EEF2FA"
FOOTER_EDGE = "#1F3864"

# --------------------------------------------------------------------------
# Canvas
# --------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(16, 7.6), dpi=150)
ax.set_xlim(0, 160)
ax.set_ylim(0, 76)
ax.set_aspect("equal")
ax.axis("off")


# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------
def panel(x, y, w, h, *, fill, edge, lw=1.6, radius=1.4, dashed=False, z=1):
    ls = (0, (5, 3)) if dashed else "solid"
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0,rounding_size={radius}",
            linewidth=lw, edgecolor=edge, facecolor=fill,
            linestyle=ls, zorder=z, mutation_aspect=1,
        )
    )


def chip(x, y, w, h, label, color, *, fs=9, tc="white"):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0,rounding_size=0.8",
            linewidth=0, facecolor=color, zorder=5,
        )
    )
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            color=tc, fontsize=fs, fontweight="bold", zorder=6)


def text(x, y, s, *, fs=10, color=INK, weight="normal", ha="left",
         va="center", style="normal", lh=1.25):
    ax.text(x, y, s, fontsize=fs, color=color, fontweight=weight,
            ha=ha, va=va, fontstyle=style, linespacing=lh, zorder=6)


def arrow(p0, p1, *, color=MUTED, lw=2.2, dashed=False, rad=0.0):
    ls = (0, (4, 2.5)) if dashed else "solid"
    ax.add_patch(
        FancyArrowPatch(
            p0, p1, arrowstyle="-|>", mutation_scale=15,
            linewidth=lw, color=color, linestyle=ls,
            shrinkA=1, shrinkB=1,
            connectionstyle=f"arc3,rad={rad}", zorder=3,
        )
    )


def wrap(s, width):
    return "\n".join(textwrap.wrap(s, width=width)) or s


# --------------------------------------------------------------------------
# Title
# --------------------------------------------------------------------------
text(80, 72.6, "User Journey  —  A Day with the Agentic CLM Assistant",
     fs=21, weight="bold", ha="center")
text(80, 68.4,
     "Six steps in one contract manager's day — each grounded, "
     "human-approved, and traced end to end.",
     fs=11.5, color=MUTED, ha="center")

# --------------------------------------------------------------------------
# Persona lane
# --------------------------------------------------------------------------
panel(3, 61.2, 154, 4.2, fill=PERSONA_FILL, edge=TEAL, lw=1.6, radius=2.0, z=2)
text(80, 63.3,
     "The Contract Manager's day   ·   lives in Microsoft 365 Copilot & Teams",
     fs=11.5, weight="bold", color="#0A5F70", ha="center")

# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------
STEPS = [
    ("Request a draft",
     "\u201cDraft a mutual NDA with Acme, 2-yr term.\u201d",
     "Intake & Drafting agent \u2014 Claude",
     "Drafts from an approved template \u00b7 grounded agent + tools",
     "Built in C1", CLAUDE),
    ("Check their draft",
     "Uploads Acme's counter-draft MSA",
     "Clause & Risk agent \u2014 Claude",
     "Scores every clause against the Standard Clause Library",
     "Built in C3", CLAUDE),
    ("Ask, with citations",
     "\u201cWhat's our standard indemnity cap?\u201d",
     "Foundry IQ",
     "Answers over the Contoso corpus \u2014 with sources",
     "Built in C1", TOOLS),
    ("Review & sign off",
     "Reads flags + citations, edits, approves",
     "Human-in-the-loop",
     "Nothing is finalized without human sign-off",
     "Built in C1\u00b7C3", HITL),
    ("Track obligations",
     "What's coming due, and when?",
     "Obligation & Renewal \u2014 GPT-4o-mini",
     "Reads status & renewals \u2014 Azure SQL, seed fallback",
     "Built in C4", GPT),
    ("Proactive alert",
     "Gets a Teams ping before the renewal date",
     "Publish + proactive messaging",
     "Renew in time \u2014 no missed auto-renewals",
     "Built in C4", TEAL),
]

X0, COLW, GAP = 3.0, 24.0, 2.0
TOP_Y, TOP_H = 47.5, 11.5
BOT_Y, BOT_H = 18.5, 24.0
BADGE_CY = 45.4

for i, (title_s, quote, mech, cap, tag, color) in enumerate(STEPS):
    x = X0 + i * (COLW + GAP)
    cx = x + COLW / 2

    # forward connector to the next step (along the badge spine)
    if i < len(STEPS) - 1:
        arrow((x + COLW + 0.1, BADGE_CY), (x + COLW + GAP - 0.1, BADGE_CY),
              color="#8A94A6", lw=2.2)

    # top card — what the manager does
    panel(x, TOP_Y, COLW, TOP_H, fill=PERSONA_FILL, edge=TEAL, lw=1.3,
          radius=1.2, z=3)
    text(cx, TOP_Y + TOP_H - 2.6, title_s, fs=11, weight="bold", ha="center",
         color="#0A5F70")
    text(cx, TOP_Y + 3.6, wrap(quote, 26), fs=8.6, color="#374151",
         ha="center", style="italic", lh=1.2)

    # number badge on the spine
    ax.add_patch(Circle((cx, BADGE_CY), 2.6, facecolor=color, edgecolor="white",
                        linewidth=1.6, zorder=5))
    ax.text(cx, BADGE_CY, str(i + 1), ha="center", va="center", color="white",
            fontsize=14, fontweight="bold", zorder=6)

    # bottom card — under the hood
    panel(x, BOT_Y, COLW, BOT_H, fill=CARD_FILL, edge=color, lw=1.8,
          radius=1.2, z=3)
    # colour accent bar along the top of the card
    ax.add_patch(FancyBboxPatch(
        (x + 0.6, BOT_Y + BOT_H - 1.4), COLW - 1.2, 0.9,
        boxstyle="round,pad=0,rounding_size=0.4", linewidth=0,
        facecolor=color, zorder=4))
    text(cx, BOT_Y + BOT_H - 4.0, wrap(mech, 24), fs=9.6, weight="bold",
         color=color, ha="center", lh=1.15)
    text(cx, BOT_Y + BOT_H - 11.4, wrap(cap, 28), fs=8.5, color=MUTED,
         ha="center", va="center", lh=1.28)
    cw = 12.5 if "\u00b7" in tag else 11.5
    chip(cx - cw / 2, BOT_Y + 1.4, cw, 3.4, tag, color, fs=8.4)

# proactive alert — the system pushes up to the manager on the final step
cx6 = X0 + 5 * (COLW + GAP) + COLW / 2
arrow((cx6, TOP_Y + TOP_H + 0.1), (cx6, 61.05), color=TEAL, lw=2.0,
      dashed=True)

# --------------------------------------------------------------------------
# Footer — one Foundry project across every step
# --------------------------------------------------------------------------
panel(3, 9.6, 154, 5.6, fill=FOOTER_FILL, edge=FOOTER_EDGE, lw=1.6,
      radius=1.6, z=2)
text(80, 13.0, "One Microsoft Foundry project across every step",
     fs=11.5, weight="bold", color=FOOTER_EDGE, ha="center")
text(80, 11.0,
     "traced \u00b7 Application Insights      evaluated \u00b7 C2      "
     "guarded by Content Safety \u00b7 C5",
     fs=9.5, color=MUTED, ha="center")

# --------------------------------------------------------------------------
# Legend
# --------------------------------------------------------------------------
LEG = [
    (CLAUDE, "Claude agent", False),
    (GPT, "GPT agent", False),
    (TOOLS, "Foundry IQ / tools", False),
    (HITL, "Human sign-off", False),
    (TEAL, "proactive alert", True),
]
lx = 30.0
for color, label, dashed in LEG:
    if dashed:
        ax.plot([lx, lx + 3.4], [4.6, 4.6], color=color, lw=2.0,
                linestyle=(0, (4, 2.5)), zorder=4)
    else:
        ax.add_patch(FancyBboxPatch(
            (lx, 3.5), 2.6, 2.2, boxstyle="round,pad=0,rounding_size=0.5",
            linewidth=0, facecolor=color, zorder=4))
    text(lx + (4.0 if dashed else 3.4), 4.6, label, fs=9.2, color=INK)
    lx += 4.0 + len(label) * 1.55 + 4.5

# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
fig.savefig(OUT / "user-journey.svg", bbox_inches="tight", pad_inches=0.1,
            transparent=False)
fig.savefig(OUT / "user-journey.png", bbox_inches="tight", pad_inches=0.1,
            dpi=150, facecolor="white")
print(f"Wrote {OUT / 'user-journey.svg'}")
print(f"Wrote {OUT / 'user-journey.png'}")
