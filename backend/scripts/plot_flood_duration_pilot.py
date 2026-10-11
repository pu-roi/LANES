"""Render conventional Matplotlib figures from the saved research pilot only."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator


def save_figure(fig: plt.Figure, output: Path, name: str) -> None:
    for extension in ("png", "svg", "pdf"):
        fig.savefig(output / f"{name}.{extension}", dpi=300, facecolor="white")
    plt.close(fig)


def render_pilot_figures(output: Path) -> None:
    summary = json.loads((output / "coverage.json").read_text(encoding="utf-8"))
    candidates = json.loads((output / "candidate_incidents.json").read_text(encoding="utf-8"))
    # Default Python scientific plotting style, shared by every export format.
    with plt.style.context("default"):
        years = [str(year) for year in range(2021, 2027)]
        counts = [summary["observation_year_counts"].get(year, 0) for year in years]
        fig, ax = plt.subplots(figsize=(9, 5.4))
        fig.subplots_adjust(left=0.12, right=0.96, bottom=0.23, top=0.86)
        bars = ax.bar(years, counts, color="tab:blue", width=0.65, zorder=3)
        ax.set_title("Pasig flood-report pilot: observations by year", pad=15)
        ax.set_xlabel("Observation year", labelpad=9)
        ax.set_ylabel("Number of extracted observations", labelpad=9)
        ax.set_ylim(0, max(counts + [1]) * 1.18)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(axis="y", color="0.85", linewidth=0.7, zorder=0)
        for bar, year, count in zip(bars, years, counts):
            collected = year in summary["observation_year_counts"]
            ax.annotate(str(count) if collected else "Not collected",
                        (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 6), textcoords="offset points", ha="center", fontsize=9)
        fig.text(0.12, 0.09, "Selected official reports only; counts are observations, not independent storms.", fontsize=9)
        fig.text(0.12, 0.052, "2021–2023 archive coverage is unverified. This figure does not show model accuracy.", fontsize=9)
        save_figure(fig, output, "coverage")

        groups: dict[str, list[dict]] = defaultdict(list)
        for candidate in candidates:
            groups[candidate["episode_group"]].append(candidate)
        fig, ax = plt.subplots(figsize=(10, 5.8))
        fig.subplots_adjust(left=0.28, right=0.94, bottom=0.34, top=0.84)
        labels = []
        maximum = 1.0
        for index, (_, records) in enumerate(sorted(groups.items())):
            record = records[0]
            # A shared interval is required; do not silently conceal differing bounds.
            bounds = {(r["remaining_hours_low"], r["remaining_hours_high"],
                       r["remaining_low_inclusive"], r["clearance_upper_inclusive"]) for r in records}
            if len(bounds) != 1:
                raise ValueError("An episode has differing bounds; split it before plotting")
            low, high, low_inclusive, high_inclusive = bounds.pop()
            maximum = max(maximum, high)
            places = sorted({r["barangay"] for r in records})
            place = places[0] if len(places) == 1 else "Multiple barangays"
            date = datetime.fromisoformat(record["last_observed_wet_at"]).strftime("%d %b %Y")
            labels.append(f"{place}\n{date} · {len(records)} location{'s' if len(records) != 1 else ''}")
            ax.hlines(index, low, high, color="tab:blue", linewidth=2.5, zorder=3)
            for value, inclusive in ((low, low_inclusive), (high, high_inclusive)):
                ax.plot(value, index, "o", color="tab:blue", markersize=7,
                        markerfacecolor="tab:blue" if inclusive else "white", zorder=4)
            minutes = round(high * 60)
            duration = f"{minutes // 60} h" + (f" {minutes % 60} min" if minutes % 60 else "")
            ax.annotate(("≤ " if high_inclusive else "< ") + duration,
                        (high, index), xytext=(10, 0), textcoords="offset points",
                        va="center", fontsize=10)
        ax.set_yticks(range(len(labels)), labels)
        ax.set_ylim(len(labels) - 0.5, -0.5)
        ax.set_xlim(-0.15, maximum * 1.2)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_xlabel("Hours after the last supported wet observation", labelpad=10)
        ax.set_title("Pasig pilot: candidate remaining-time intervals", pad=16)
        ax.grid(axis="x", color="0.85", linewidth=0.7, zorder=0)
        ax.legend(handles=[
            Line2D([], [], marker="o", color="tab:blue", linestyle="None", markerfacecolor="white", label="Endpoint excluded"),
            Line2D([], [], marker="o", color="tab:blue", linestyle="None", label="Endpoint included"),
        ], loc="upper left", bbox_to_anchor=(0, -0.28), ncol=2, frameon=False, fontsize=9)
        fig.text(0.08, 0.08, "Bounds inferred from shared clearance summaries; unknown onset and exact clearance time.", fontsize=9)
        fig.text(0.08, 0.043, "Locations share evidence. These are candidate intervals, not predictions or total flood durations.", fontsize=9)
        save_figure(fig, output, "clearance_bounds")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    args = parser.parse_args()
    render_pilot_figures(args.bundle)
    print(f"Saved PNG, SVG and PDF figures in {args.bundle}")


if __name__ == "__main__":
    main()
