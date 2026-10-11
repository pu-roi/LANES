"""Export standard Matplotlib coverage and candidate-interval research figures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

from plot_flood_duration_pilot import save_figure


def render(output: Path) -> None:
    coverage = json.loads((output / "coverage.json").read_text(encoding="utf-8"))
    bounds = json.loads((output / "candidate_clearance_bounds.json").read_text(encoding="utf-8"))
    years = [str(y) for y in coverage["target_years"]]
    counts = coverage["city_year_evidence_counts"]
    with plt.style.context("default"):
        fig, ax = plt.subplots(figsize=(9, 5.5))
        fig.subplots_adjust(left=.12, right=.96, top=.85, bottom=.24)
        values = [counts["Pasig"].get(y, 0) for y in years]
        historical = [coverage["historical_city_year_counts"]["Pasig"].get(y, 0) for y in years]
        direct = [v-h for v,h in zip(values,historical)]
        ax.bar(years,direct,color="tab:blue",zorder=3,label="Flood-report observations")
        bars = ax.bar(years,historical,bottom=direct,color="tab:orange",zorder=3,label="Historical incident records")
        for bar, value in zip(bars, values):
            ax.annotate(str(value) if value else "Capture gap", (bar.get_x()+bar.get_width()/2, value), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=10)
        ax.set_title("Pasig: collected flood evidence, 2021–2026", pad=16)
        ax.set_ylabel("Source-linked evidence records (rows)")
        ax.legend(loc="upper left",fontsize=9)
        ax.set_xlabel("Year in reported evidence")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_ylim(0, max(values)*1.17)
        ax.grid(axis="y", alpha=.25, zorder=0)
        fig.text(.12,.07,"2023 gap does not mean no flooding. 2026 is partial through 4 October.\nSelected sources; incident occurrence times are not clearance times.",fontsize=9)
        save_figure(fig, output, "pasig-year-coverage")

        cities = list(counts)
        matrix = np.array([[counts[city].get(y, 0) for y in years] for city in cities])
        fig, ax = plt.subplots(figsize=(9.4, 9))
        fig.subplots_adjust(left=.23, right=.86, top=.90, bottom=.15)
        plotted = np.ma.masked_where(matrix == 0, matrix)
        cmap = plt.get_cmap("Blues").copy()
        cmap.set_bad("#eeeeee")
        im = ax.imshow(plotted, aspect="auto", cmap=cmap, vmin=0, vmax=matrix.max())
        for i in range(len(cities)):
            for j in range(len(years)):
                value = matrix[i,j]
                ax.text(j,i,str(value) if value else "—",ha="center",va="center",fontsize=10,color="white" if value>matrix.max()*.6 else "black")
        ax.set_xticks(range(len(years)),years)
        ax.set_yticks(range(len(cities)),cities)
        ax.set_xlabel("Year in reported evidence")
        ax.set_title("NCR: collected flood evidence by local government",pad=18)
        fig.colorbar(im,ax=ax,fraction=.035,pad=.04,label="Evidence records")
        fig.text(.23,.055,f"— = no evidence collected in this snapshot; not absence of flooding.\n{coverage['covered_lgus']} of 17 LGUs represented. Source selection is partial; 2026 is year to date.",fontsize=9)
        save_figure(fig, output, "ncr-city-year-coverage")

        fig, ax = plt.subplots(figsize=(10.5, 5.8))
        fig.subplots_adjust(left=.36, right=.95, top=.84, bottom=.25)
        labels = []
        for i,bound in enumerate(bounds):
            high = bound["remaining_minutes_high"]
            ax.hlines(i,0,high,color="tab:blue",linewidth=2)
            ax.plot(0,i,"o",color="tab:blue",markerfacecolor="white")
            ax.plot(high,i,"o",color="tab:blue")
            ax.annotate(f"≤ {high:g} min",(high,i),xytext=(6,0),textcoords="offset points",va="center",fontsize=9)
            location = bound["location_raw"].replace("Along Taft Avenue from Pedro Gil to in front of PGH", "Taft: Pedro Gil–PGH")
            labels.append(location+"\n"+bound["last_wet_at"][:10])
        ax.set_yticks(range(len(bounds)),labels,fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(-3,max(b["remaining_minutes_high"] for b in bounds)+22)
        ax.set_xlabel("Possible remaining time after last wet report (minutes)")
        ax.set_title("Manila: candidate report-based clearance intervals",pad=16)
        ax.grid(axis="x",alpha=.25)
        ax.legend(handles=[Line2D([0],[0],marker="o",markerfacecolor="white",color="tab:blue",linestyle="None",label="Open lower bound"),Line2D([0],[0],marker="o",color="tab:blue",linestyle="None",label="Reported upper bound")],loc="upper right",fontsize=8)
        fig.text(.13,.06,"Five location pairs share two dates. Onset is unknown; these are candidate remaining-time bounds,\nnot total flood durations, model predictions, or measured accuracy.",fontsize=9)
        save_figure(fig,output,"ncr-candidate-clearance-bounds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    render(parser.parse_args().output)
