"""Draw five HYPOTHETICAL trends, not experimental results.

Run: python3 figures/draw_analysis_hypotheses.py
All vertical coordinates below are arbitrary dimensionless drawing coordinates.
They are not accuracies, KL measurements, fitted predictions, or confidence bounds.
This script must not be used to populate result tables. Replace it with a real
results-driven plotter once the pre-registered experiments have been run.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).resolve().parent
TEAL = "#087E8B"
BLUE = "#326BC5"
ORANGE = "#CE7340"
MUTED = "#596B7C"
LINE = "#D5DEE7"


def frame(xlabel: str, ylabel: str):
    fig, ax = plt.subplots(figsize=(8.2, 3.6), facecolor="white")
    fig.subplots_adjust(left=0.12, right=0.97, bottom=0.23, top=0.78)
    fig.text(0.5, 0.94, "HYPOTHESIS ONLY - NOT EXPERIMENTAL RESULTS",
             ha="center", fontsize=13, weight="bold", color=ORANGE)
    fig.text(0.5, 0.855, "Illustrative shapes; no numerical performance or uncertainty implied",
             ha="center", fontsize=10, color=MUTED)
    ax.set(xlabel=xlabel, ylabel=ylabel, ylim=(0.10, 1.05))
    ax.set_yticks([])
    ax.spines[["top", "right"]].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(LINE)
    ax.tick_params(axis="x", labelsize=11, colors=MUTED)
    ax.xaxis.label.set_size(12)
    ax.yaxis.label.set_size(11)
    ax.text(0.5, 0.43, "SCHEMATIC", transform=ax.transAxes, ha="center",
            fontsize=25, color=LINE, alpha=0.7, zorder=0)
    return fig, ax


def save(fig, name: str, note: str) -> None:
    fig.text(0.5, 0.035, note, ha="center", fontsize=10, color=MUTED)
    for extension in ["pdf", "svg"]:
        fig.savefig(OUT / f"hypothesis_{name}.{extension}", facecolor="white")
    plt.close(fig)


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "stix",
                         "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none"})
    x = np.linspace(0, 1, 101)
    fig, ax = frame(r"Output shrinkage $\alpha$", "Mean accuracy (schematic)")
    y = 0.48 + 0.48 * (1 - np.exp(-6 * x)) - 0.62 * x ** 1.4
    ax.plot(x, y, color=TEAL, lw=2.5)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.text(0.24, 0.85, "Possible stability / direction trade-off", fontsize=11, color=TEAL)
    save(fig, "shrinkage", "Automatic shrinkage is a separate reference, not a fixed alpha on this curve.")

    fig, ax = frame("Statistics samples per task", "Mean accuracy (schematic)")
    sizes = [32, 64, 128, 256]
    ax.plot(sizes, [0.46, 0.67, 0.80, 0.84], "o-", color=TEAL, lw=2.2,
            label="INK-Merge (hypothesis)")
    ax.plot(sizes, [0.37, 0.52, 0.61, 0.65], "s--", color=BLUE, lw=2,
            label="Current Fisher (hypothesis)")
    ax.set_xscale("log", base=2)
    ax.set_xticks(sizes, [str(n) for n in sizes])
    ax.legend(loc="lower right", fontsize=10, frameon=False)
    save(fig, "samples", "Nested statistics subsets; the same 256 held-out samples at every setting.")

    fig, ax = frame("Update round", "Independent teacher KL (schematic)")
    rounds = [0, 1, 2, 3, 4]
    ax.plot(rounds, [0.92, 0.64, 0.55, 0.51, 0.50], "s--", color=BLUE, lw=2,
            label="Dynamic current Fisher")
    ax.plot(rounds, [0.92, 0.56, 0.47, 0.44, 0.44], "^--", color=MUTED, lw=2,
            label="Frozen initial G; updated A")
    ax.plot(rounds, [0.92, 0.56, 0.38, 0.29, 0.26], "o-", color=TEAL, lw=2.2,
            label="Dynamic A and G (INK-Merge)")
    ax.set_xticks(rounds)
    ax.legend(loc="upper right", fontsize=9.5, frameon=False)
    save(fig, "rounds", "Same initialization; frozen-G and full method share the first update in this hypothesis.")

    omega = np.linspace(0, 1, 11)
    fig, ax = frame(r"Single-round interpolation $\omega$", "Mean accuracy (schematic)")
    ax.plot(omega, [0.42, 0.56, 0.70, 0.79, 0.82, 0.79, 0.73, 0.63, 0.50, 0.36, 0.22],
            "o-", color=TEAL, lw=2.2)
    ax.set_xticks(omega, [f"{v:.1f}" for v in omega])
    ax.text(0.13, 0.96, "An interior step could outperform full replacement", fontsize=10.5, color=TEAL)
    save(fig, "step_accuracy", "0 = initialization (not Zero-shot); 1 = candidate. No selected-step marker is shown.")

    fig, ax = frame(r"Single-round interpolation $\omega$", "Independent teacher KL (schematic)")
    ax.plot(omega, [0.82, 0.61, 0.43, 0.34, 0.36, 0.41, 0.50, 0.60, 0.71, 0.81, 0.92],
            "o-", color=BLUE, lw=2.2)
    ax.set_xticks(omega, [f"{v:.1f}" for v in omega])
    ax.text(0.10, 1.0, "KL could rebound as the candidate is fully applied", fontsize=10.5, color=BLUE)
    save(fig, "step_kl", "The KL trough need not coincide with the accuracy peak or the held-out selected step.")


if __name__ == "__main__":
    main()
