# Shared figure style for every WindMap plot: journal-like fonts, ticks and sizes.
import matplotlib as mpl

TEXT_WIDTH_IN = 6.3   # A4 page text width with 2.5 cm margins [in]; figures drawn at print size

# Colour-blind-checked palette, always used in this order (blue, orange, aqua, yellow, magenta, green)
COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]


def apply():
    """Call once at the start of a figure script."""
    mpl.rcParams.update({
        # Serif text and maths that match a LaTeX report (STIX ships with Matplotlib, no LaTeX needed)
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 9,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        # Thin frame, ticks inside on all four sides, minor ticks on
        "axes.linewidth": 0.8,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,
        # Lines, legend, saving
        "lines.linewidth": 1.5,
        "lines.markersize": 4,
        "legend.frameon": False,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })