"""Rebuild the INK-Merge overview: python3 figures/draw_method_overview.py.

All geometry is illustrative; the equations follow chaps/3-method.tex.
The layer index ell is suppressed, and G denotes G_{t,ink}^{ell,(r)}.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Circle
from matplotlib.path import Path as MplPath


OUT = Path(__file__).resolve().parent
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "mathtext.fontset": "stix",
    "font.size": 15,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})

NAVY = "#142D4E"
MUTED = "#596B7C"
BLUE = "#326BC5"
TEAL = "#087E8B"
PURPLE = "#7444AF"
GREEN = "#2A7955"
ORANGE = "#CE7340"
LINE = "#D5DEE7"
fig, ax = plt.subplots(figsize=(16, 7.4))
fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
ax.set(xlim=(0, 16), ylim=(7.4, 0))
ax.set_aspect("equal")
ax.axis("off")
fig.patch.set_facecolor("white")


def text(x, y, value, size=15, color=NAVY, weight="normal", ha="left", **kwargs):
    return ax.text(x, y, value, fontsize=size, color=color, weight=weight,
                   ha=ha, va="center", **kwargs)


def box(x, y, w, h, color=LINE, fill="white", lw=1.2, radius=0.13):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=fill, edgecolor=color, linewidth=lw, zorder=1,
    ))


def arrow(points, color=NAVY, lw=1.6, dashed=False, head=13):
    path = MplPath(points, [MplPath.MOVETO] + [MplPath.LINETO] * (len(points) - 1))
    ax.add_patch(FancyArrowPatch(path=path, arrowstyle="-|>",
                               mutation_scale=head, color=color, lw=lw,
                               linestyle=(0, (3, 3)) if dashed else "-",
                               zorder=3, capstyle="round", joinstyle="round"))


def section(x, number, title):
    box(x, 0.78, 0.34, 0.34, NAVY, NAVY, radius=0.08)
    text(x + 0.17, 0.955, number, 12, "white", "bold", ha="center")
    text(x + 0.46, 0.95, title, 18, weight="bold")


def network(cx, cy, color):
    columns = [(cx - 0.28, [-0.23, 0.23]),
               (cx, [-0.4, 0, 0.4]),
               (cx + 0.28, [-0.23, 0.23])]
    for left, right in zip(columns, columns[1:]):
        for a in left[1]:
            for b in right[1]:
                ax.plot([left[0], right[0]], [cy + a, cy + b],
                        color=color, alpha=0.45, lw=1, zorder=2)
    for x, ys in columns:
        for y in ys:
            ax.add_patch(Circle((x, cy + y), 0.072, ec=color, fc="white", lw=1.1, zorder=3))


def geometry(cx, cy, color, angle):
    ax.add_patch(Ellipse((cx, cy), 1.35, 0.64, angle=angle,
                         fc=color, alpha=0.09, ec="none", zorder=2))
    ax.add_patch(Ellipse((cx, cy), 1.35, 0.64, angle=angle,
                         fill=False, ec=color, lw=1.1, zorder=2))
    if angle < 0:
        directions = [(-0.49, 0.2), (0.49, -0.2), (-0.12, -0.23), (0.12, 0.23)]
    else:
        directions = [(-0.49, -0.2), (0.49, 0.2), (0.12, -0.23), (-0.12, 0.23)]
    for dx, dy in directions:
        arrow([(cx, cy), (cx + dx, cy + dy)], color, 1.05, head=8)
    ax.add_patch(Circle((cx, cy), 0.045, fc=color, ec="none", zorder=4))


# Header: one method name and one sentence of motivation.
text(0.25, 0.33, "INK-Merge", 24, weight="bold")
text(2.38, 0.35, "Merge with the functional corrections the current model still needs", 17, MUTED)
section(0.25, "1", "Models & signals")
section(3.48, "2", "Residual-driven geometry")
section(11.15, "3", "Merge & validate")

# Shared calibration inputs and the two model states.
box(0.25, 1.38, 2.55, 0.64, fill="#F4F7FA")
text(1.525, 1.60, "Unlabeled calibration", 14, weight="bold", ha="center")
text(1.525, 1.85, r"$x\in\mathcal{C}_t$", 18, ha="center")

box(0.25, 2.39, 2.55, 1.38, BLUE, "#F4F8FE")
text(0.44, 2.68, "Frozen experts", 16, BLUE, "bold")
network(0.77, 3.23, BLUE)
text(1.98, 3.10, r"$\{\theta_t\}_{t=1}^{T}$", 22, BLUE, ha="center")
text(1.98, 3.51, "cached predictions", 10.5, MUTED, ha="center")

box(0.25, 4.66, 2.55, 1.61, NAVY, "#F4F7FA", lw=1.5)
text(0.44, 4.96, "Current merge", 16, weight="bold")
network(0.77, 5.62, NAVY)
text(1.98, 5.46, r"$\theta^{(r)}$", 26, ha="center")
text(1.98, 5.95, "forward pass", 12, MUTED, ha="center")

arrow([(1.52, 2.02), (1.52, 2.39)], MUTED)
arrow([(0.25, 1.7), (0.09, 1.7), (0.09, 5.45), (0.25, 5.45)], MUTED, lw=1.1)

# Main contribution: class residual -> normalized feature-space correction.
box(3.48, 1.65, 7.20, 2.51, PURPLE, "#F8F5FC", lw=1.5)
text(3.70, 1.96, "From prediction mismatch to a layerwise correction", 17, PURPLE, "bold")

text(4.93, 2.38, r"$e_{t,c}^{(r)}=p_{t,c}-q_c^{(r)}$", 22, ha="center")
ax.plot([3.96, 5.91], [3.07, 3.07], color=LINE, lw=1, zorder=2)
for i, value in enumerate([0.33, -0.21, 0.13, -0.25]):
    xpos = 4.14 + i * 0.49
    ax.bar(xpos, -value, bottom=3.07, width=0.23,
           color=BLUE if value > 0 else ORANGE, zorder=3)
text(4.93, 3.62, "Signed class residuals", 13, MUTED, ha="center")
arrow([(6.00, 2.86), (6.48, 2.86)], PURPLE, lw=1.4)
text(8.47, 2.64,
     r"$u_t^{(r)}=-\frac{\nabla_{h_\ell}D_{\mathrm{KL}}(p_t\Vert q^{(r)})}{d_t^{(r)}}$",
     27, PURPLE, ha="center")
text(8.47, 3.45,
     r"$d_t^{(r)}=\sqrt{\sum_c\frac{(e_{t,c}^{(r)})^2}{q_c^{(r)}}+\varepsilon}$",
     22, ha="center")
text(8.47, 3.94, "Pearson normalization  ·  stop gradient through d", 12, MUTED, ha="center")

# Signals enter separately so teacher predictions cannot be mistaken for activations.
arrow([(2.80, 3.02), (3.12, 3.02), (3.12, 2.53), (3.48, 2.53)], BLUE)
text(3.10, 2.30, r"$p_t$", 20, BLUE, ha="center")
arrow([(2.80, 5.02), (3.24, 5.02), (3.24, 3.65), (3.48, 3.65)], NAVY)
text(3.02, 4.51, r"$q^{(r)}$", 19, ha="center")

# Both factors are measured at the current merge.
box(3.48, 4.69, 3.45, 1.58, TEAL, "#F1F9F9")
text(3.68, 4.96, "Input geometry", 16, TEAL, "bold")
geometry(4.34, 5.57, TEAL, 23)
text(5.91, 5.52, r"$A_t^{(r)}=\mathbb{E}[hh^\top]$", 21, TEAL, ha="center")
text(5.91, 5.95, r"$h=h_{\ell-1}$", 17, MUTED, ha="center")
arrow([(2.80, 5.66), (3.48, 5.66)], TEAL)
text(3.14, 5.40, r"$h_{\ell-1}$", 16, TEAL, ha="center")

box(7.23, 4.69, 3.45, 1.58, PURPLE, "#F8F5FC")
text(7.43, 4.96, "Correction geometry", 16, PURPLE, "bold")
geometry(8.02, 5.54, PURPLE, -23)
text(9.53, 5.53, r"$G_t^{(r)}=\mathbb{E}[u_tu_t^\top]$", 21, PURPLE, ha="center")
text(8.96, 6.05, r"$p_t=q^{(r)}\;\Rightarrow\;u_t=0$", 17, PURPLE, ha="center")
arrow([(8.96, 4.16), (8.96, 4.69)], PURPLE)
text(9.18, 4.43, "second moment", 12, MUTED)

# Frozen expert parameters are explicit anchors of the layerwise solve.
arrow([(2.80, 2.70), (2.94, 2.70), (2.94, 1.30), (13.25, 1.30), (13.25, 1.65)], BLUE, 1.15, dashed=True)
text(7.25, 1.30, r"Expert weight anchors  $X_t=(W_t^\ell)^\top$", 13, BLUE,
     ha="center", bbox={"facecolor": "white", "edgecolor": "none", "pad": 2})

box(11.15, 1.65, 4.60, 2.25, NAVY, "#F4F7FA", lw=1.5)
text(11.37, 1.96, "Two-sided layerwise solve", 17, weight="bold")
text(13.45, 2.71,
     r"$\sum_t A_t^{(r)}X^\star G_t^{(r)}$" + "\n" +
     r"$=\sum_t A_t^{(r)}X_t G_t^{(r)}$", 23, ha="center", linespacing=1.5)
text(13.45, 3.57, "Matrix-free preconditioned CG", 13, MUTED, ha="center")

# Route both factors under the cards, then into the solver.
arrow([(5.20, 6.27), (5.20, 6.53), (10.91, 6.53), (10.91, 3.19), (11.15, 3.19)], TEAL, 1.25)
arrow([(10.68, 5.55), (10.91, 5.55)], PURPLE, 1.4, head=9)

box(11.15, 4.43, 4.60, 1.84, GREEN, "#F3F9F5", lw=1.5)
text(11.37, 4.73, "Held-out teacher-KL line search", 16, GREEN, "bold")
text(13.45, 5.16,
     r"$W_b^{(r+1)}=W_b^{(r)}+\omega_b(W_b^\star-W_b^{(r)})$",
     19, ha="center")
text(13.45, 5.60, r"$\omega_b\in\Omega\subseteq[0,1],\quad 0\in\Omega$", 19, GREEN, ha="center")
text(13.45, 6.02, r"Disjoint $\mathcal{H}_t$  ·  zero step can reject an update", 12, MUTED, ha="center")
arrow([(13.45, 3.90), (13.45, 4.43)], NAVY)
text(13.68, 4.16, r"candidate $\theta^\star$", 15)

# Re-estimation is the outer loop, not an iterative solve of fixed factors.
arrow([(12.38, 6.27), (12.38, 6.95), (1.53, 6.95), (1.53, 6.27)], NAVY, 1.9)
text(7.23, 6.95, r"Update $q^{(r+1)}$ and re-estimate both $A$ and $G$", 17, weight="bold",
     ha="center", bbox={"facecolor": "white", "edgecolor": "none", "pad": 5})
box(13.10, 6.67, 2.65, 0.55, GREEN, "#F3F9F5", lw=1.2)
arrow([(14.43, 6.27), (14.43, 6.67)], GREEN, 1.3)
text(14.43, 6.945, r"Best held-out round $\widehat\theta$", 13, GREEN, ha="center")

for ext in ("pdf", "svg", "png"):
    fig.savefig(OUT / f"ink_method_overview.{ext}", dpi=240, facecolor="white")
plt.close(fig)
print(f"Wrote PDF, SVG, and PNG to {OUT}")
