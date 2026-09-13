"""Render paper figures/tables from archived measurements, without model runs.

Run from the repository root: python3 motivation_method/make_figures.py
Dependencies: NumPy, Matplotlib and a TeX distribution with Fandol fonts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np


ROOT = Path(__file__).resolve().parent
COLORS = {"Average": "#C66B2B", "RegMean": "#268376", "Iso-C": "#356CB0"}
ORDER = ("Average", "RegMean", "Iso-C")
START_KEYS = {"Average": "average", "RegMean": "regmean", "Iso-C": "isoc"}


def configure_fonts(path: Path | None = None) -> None:
    if path is None:
        result = subprocess.run(
            ["kpsewhich", "FandolSong-Regular.otf"],
            check=True, text=True, capture_output=True,
        )
        path = Path(result.stdout.strip())
    if not path.is_file():
        raise FileNotFoundError("Install the TeX Fandol font package before rendering.")
    font_manager.fontManager.addfont(str(path))
    family = font_manager.FontProperties(fname=str(path)).get_name()
    plt.rcParams.update({
        "font.family": ["DejaVu Sans", family],
        "font.size": 10.5,
        "axes.titlesize": 11.5,
        "axes.labelsize": 10.5,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "axes.edgecolor": "#555555",
        "axes.labelcolor": "#262626",
        "text.color": "#202020",
        "xtick.color": "#444444",
        "ytick.color": "#444444",
        "axes.unicode_minus": False,
        # CFF/OpenType cannot be embedded as a TrueType Type 42 font.
        "pdf.fonttype": 42 if path.suffix.lower() in {".ttf", ".ttc"} else 3,
        "ps.fonttype": 42 if path.suffix.lower() in {".ttf", ".ttc"} else 3,
        "savefig.facecolor": "white",
    })


def save(fig: plt.Figure, name: str) -> None:
    # Vector PDFs are manuscript assets; previews can be regenerated locally.
    fig.savefig(ROOT / "figures" / f"{name}.pdf", metadata={
        "Title": name, "Creator": "Matplotlib; archived ViT-B/32 seed 0 data",
        "CreationDate": None, "ModDate": None,
    })
    fig.savefig(ROOT / "figures" / f"{name}.png", dpi=200)
    plt.close(fig)


def motivation(data: dict) -> None:
    pair = json.loads((ROOT / "data/fisher_first_round.json").read_text())
    assert pair["student"]["initial_checkpoint_sha256"] == pair["expert"]["initial_checkpoint_sha256"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.55))
    fig.subplots_adjust(left=.085, right=.99, bottom=.22, top=.86, wspace=.38)
    ax = axes[0]
    for name, label, color, marker in [
        ("student", "学生 A/G", COLORS["RegMean"], "o"),
        ("expert", "专家 A/G", COLORS["Average"], "s"),
    ]:
        trials = pair[name]["trials"]
        steps = [t["scaling"] for t in trials]
        assert steps == [0, .125, .25, .5, 1]
        ax.plot(steps, [t["mean_teacher_kl"] for t in trials], marker + "-",
                color=color, lw=1.6, ms=4, label=label)
    ax.set(title="(a) 测量位置", xlabel="首轮提案插值系数 ω", ylabel="留出教师 KL（越低越好）",
           xlim=(-.03, 1.03), ylim=(.13, .36), xticks=[0, .125, .25, .5, 1])
    ax.set_xticklabels(["0", ".125", ".25", ".5", "1"])
    ax.legend(loc="upper right", frameon=False)
    ax = axes[1]
    tr = data["refresh"]["Average"]["trajectory"]
    fresh = [tr[f"refreshed_{i}"]["test_accuracy"] for i in range(1, 5)]
    frozen = [fresh[0]] + [tr[f"frozen_{i}"]["test_accuracy"] for i in range(2, 5)]
    ax.plot(range(1, 5), fresh, "o-", color=COLORS["RegMean"], ms=4, lw=1.6, label="刷新 A/G")
    ax.plot(range(1, 5), frozen, "s-", color=COLORS["Average"], ms=4, lw=1.4, label="冻结 A/G")
    ax.axhline(tr["one_shot_cg400"]["test_accuracy"], ls="--", lw=1.1,
               color="#6B7280", label="单轮 CG400")
    ax.set(title="(b) 继续更新与重新测量", xlabel="外层轮次", ylabel="测试准确率 (%)",
           xlim=(.9, 4.15), ylim=(83.5, 85.55), xticks=range(1, 5), yticks=[83.5, 84.5, 85.5])
    ax.legend(loc="lower right", frameon=False, labelspacing=.25)
    for ax in axes:
        ax.grid(axis="y", color="#E6E6E6", linewidth=.6, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(length=3, width=.6)
    save(fig, "motivation")


def context(data: dict) -> None:
    fig, ax = plt.subplots(figsize=(5.4, 2.25))
    fig.subplots_adjust(left=.15, right=.99, bottom=.23, top=.93)
    positions = np.arange(3)
    blocks = ("0", "5", "11")
    entries = data["refresh"]["Average"]["cross_block"]
    for offset, key, label, color in [
        (-.19, "old", "初始统计", "#8C929A"),
        (.19, "new", "当前统计", COLORS["RegMean"]),
    ]:
        values = [entries[b][key]["diagnostic_kl_gain"] for b in blocks]
        bars = ax.bar(positions + offset, values, width=.34, color=color, label=label)
        ax.bar_label(bars, labels=[f"{v:.5f}" for v in values], padding=3, fontsize=9)
    ax.set_xticks(positions, [f"Block {b}" for b in blocks])
    ax.set(ylabel="诊断 KL 降低量", ylim=(0, .049), yticks=[0, .02, .04])
    ax.legend(loc="upper left", frameon=False, borderpad=.05, handlelength=1.2)
    ax.grid(axis="y", color="#E6E6E6", linewidth=.6)
    ax.set_axisbelow(True)
    save(fig, "context")


def tables(data: dict) -> None:
    starts = [r"\begin{tabular}{lrrr}", r"\toprule",
              r"初始化 & 初始诊断 & 第四轮诊断 & 终态测试 \\", r"\midrule"]
    for name, key in [
        ("Average", "average"), ("RegMean", "regmean"),
        ("Iso-C", "isoc"), ("未拉平（范数匹配）", "unflattened_matched"),
    ]:
        entry = data["multistart"]["accuracy"][key]
        starts.append(f"{name} & {entry['diagnostic'][0]:.2f} & "
                      f"{entry['diagnostic'][4]:.2f} & {entry['test']:.2f} " + r"\\")
    starts.extend([r"\bottomrule", r"\end{tabular}"])
    (ROOT / "tables" / "starts.tex").write_text("\n".join(starts) + "\n", encoding="utf-8")

    refresh = [r"\begin{tabular}{lrrrrr}", r"\toprule",
               r"初始化 & 第一轮 & 四轮冻结 & 四轮刷新 & 单轮 CG400 & 刷新$-$冻结 \\", r"\midrule"]
    for name in ORDER:
        tr = data["refresh"][name]["trajectory"]
        values = [tr[k]["test_accuracy"] for k in
                  ["refreshed_1", "frozen_4", "refreshed_4", "one_shot_cg400"]]
        values.append(values[2] - values[1])
        refresh.append(name + " & " + " & ".join(f"{v:.3f}" for v in values) + r" \\")
    refresh.extend([r"\bottomrule", r"\end{tabular}"])
    (ROOT / "tables" / "refresh.tex").write_text("\n".join(refresh) + "\n", encoding="utf-8")


def main_tables() -> None:
    data = json.loads((ROOT / "data/main_results.json").read_text())
    get = lambda rows, name: next(row for row in rows[1:] if row[0] == name)
    clip_ref = get(data["clip_main"], "ESM")
    clip_ours = get(data["clip_main"], "Coexist-Merge（4 seed）")
    t5_ref = get(data["t5_main"], "TA + FeatCal（我们移植）")
    t5_ours = next(r for r in data["t5_main"][1:] if r[0].startswith("Coexist-Merge"))
    def score(value: str) -> str:
        clean = value.split("（", 1)[0].strip()
        return "$" + clean.replace("±", r"\pm") + "$"
    rows = [r"\begin{tabular}{llcc}", r"\toprule",
            r"设定 & 参照方法 & 参照分数 & \method{} \\", r"\midrule",
            "CLIP ViT-B/32 & ESM & " + score(clip_ref[2]) + " & " + score(clip_ours[2]) + r" \\",
            "T5-base & TA + FeatCal（移植） & " + score(t5_ref[1]) + " & " + score(t5_ours[1]) + r" \\",
            "T5-large & TA + FeatCal（移植） & " + score(t5_ref[2]) + " & " + score(t5_ours[2]) + r" \\",
            r"\bottomrule", r"\end{tabular}"]
    (ROOT / "tables/main_summary.tex").write_text("\n".join(rows) + "\n")
    rows = [r"\begin{tabular}{llrrrr}", r"\toprule",
            r"模型 & 起点 & \multicolumn{2}{c}{GSM8K} & \multicolumn{2}{c}{IFEval} \\",
            r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}",
            r" & & 起点 & 接受后 & 起点 & 接受后 \\", r"\midrule"]
    for model, name in data["paper_selection"]["llm_rows"]:
        record = get(data["llama"] if model.startswith("Llama") else data["gemma"], name)
        label = "Llama-3.2-3B" if model.startswith("Llama") else "Gemma-2-2B"
        short = name.replace("（自身默认）", "")
        rows.append(" & ".join([label, short, record[1], record[2], record[4], record[5]]) + r" \\")
    rows.extend([r"\bottomrule", r"\end{tabular}"])
    (ROOT / "tables/llm_summary.tex").write_text("\n".join(rows) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, help="Optional Chinese TrueType font (.ttf/.ttc)")
    args = parser.parse_args()
    data = json.loads((ROOT / "evidence.json").read_text(encoding="utf-8"))
    for subdir in ("figures", "tables"):
        (ROOT / subdir).mkdir(exist_ok=True)
    configure_fonts(args.font)
    motivation(data)
    context(data)
    tables(data)
    main_tables()
    print("Generated two figures and four tables from archived and supplied data.")


if __name__ == "__main__":
    main()
