"""Shared chart style, so every figure in the notebooks and the slides looks the same.

Colour rule (same in the slides and the Tableau dashboard):
- orange and navy are ONLY used for the Lisbon and Porto metro areas;
- every other chart uses the "Rest of Portugal" blue for the message and greys for everything else.
"""
import matplotlib.pyplot as plt

from src.config import FIGURES_DIR

LISBON = "#C87B29"     # azulejo orange - Lisbon metro only
PORTO = "#404F7A"      # azulejo navy - Porto metro only
REST = "#8D9DBE"       # soft azulejo blue - Rest of Portugal, and the highlight colour of other charts
AREA_COLORS = {"Lisbon metro": LISBON, "Porto metro": PORTO, "Rest of Portugal": REST}
HIGHLIGHT = REST
GREY = "#D7D6DB"
DARK_GREY = "#595959"
TEXT = "#1A1A1A"


def apply_style():
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "axes.edgecolor": GREY, "axes.labelcolor": DARK_GREY, "axes.titlecolor": TEXT,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": DARK_GREY, "ytick.color": DARK_GREY, "font.size": 11,
        "axes.grid": False, "legend.frameon": False,
    })


def save(fig, name):
    """Save a figure in figures/ at slide quality."""
    fig.savefig(FIGURES_DIR / name, bbox_inches="tight", dpi=200)


def horizontal_bars(ax, labels, values, highlight=None, value_format="{:.2f}", colors=None):
    """Sorted horizontal bars (largest on top) with the value written at the end of each bar."""
    if colors is None:
        colors = [HIGHLIGHT if label == highlight else GREY for label in labels]
    triples = sorted(zip(labels, values, colors), key=lambda triple: triple[1])
    labels, values, colors = [t[0] for t in triples], [t[1] for t in triples], [t[2] for t in triples]
    bars = ax.barh(labels, values, color=colors, height=0.6)
    for bar, value in zip(bars, values):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, " " + value_format.format(value),
                va="center", ha="left", color=TEXT, fontsize=10)
    ax.set_xlim(0, max(values) * 1.18)
    ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)
    return bars
