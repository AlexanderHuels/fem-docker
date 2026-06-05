from __future__ import annotations

import numpy as np
from matplotlib import colormaps
from matplotlib.colors import ListedColormap


ABAQUS_LIKE_HEX = [
    "#1f3b8f",  # dark blue
    "#2458c3",  # blue
    "#2f79e3",  # lighter blue
    "#3fa2f2",  # cyan-blue
    "#35c6d8",  # cyan
    "#41cf78",  # green
    "#86d63c",  # yellow-green
    "#d4da2a",  # yellow
    "#f2b52c",  # yellow-orange
    "#ee7c24",  # orange
    "#df451d",  # orange-red
    "#c81414",  # red
]


def available_colormaps():
    return ["turbo", "viridis", "abaqus"]


def build_colormap(name: str, legend_mode: str = "discrete", n_levels: int = 8):
    """
    Build a matplotlib colormap for PyVista usage.

    name:
        turbo | viridis | abaqus
    legend_mode:
        discrete | continuous
    n_levels:
        number of discrete levels if legend_mode == discrete
    """
    if n_levels < 2:
        n_levels = 2

    if name == "abaqus":
        base = ListedColormap(ABAQUS_LIKE_HEX, name="abaqus_like")
    else:
        base = colormaps[name]

    if legend_mode == "discrete":
        xs = np.linspace(0.0, 1.0, n_levels)
        return ListedColormap(base(xs), name=f"{name}_{n_levels}")

    return base
