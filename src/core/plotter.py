import enum
import logging
from tkinter import SEPARATOR
from tkinter.ttk import Separator

import geopandas
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pywaffle import Waffle

LOGGER = logging.getLogger("systematic")


class Plotter:
    # chose a colormap
    # https://matplotlib.org/2.0.2/users/colormaps.html
    def __init__(self):
        self.__df = pd.read_csv("data/df3.csv")
        # print(self.__df.head())

    def plot_bar_type(self):
        fig, ax = plt.subplots()
        self.__df.groupby(["year", "sub_type"]).size().unstack().plot.bar(
            stacked=True, ax=ax
        )
        #    stacked=True, ax=ax
        # )
        ax.set_axisbelow(True)
        ax.grid(axis="y")
        ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12))

        plt.xlabel("Publication year")
        plt.ylabel("Number of articles")
        plt.yticks(list(range(0, 25, 5)))
        plt.tight_layout()
        plt.savefig("/tmp/fig_type.svg")
        # plt.show()

    def plot_type(self):
        fig, ax = plt.subplots()
        # self.__df.groupby(["year", "sub_type"]).size().unstack().plot.bar(
        #    stacked=True, ax=ax
        # )
        # self.__df.groupby(["sub_type"]).size().plot.bar(ax=ax)
        self.__df.groupby(["sub_type"]).size().plot.pie(
            ax=ax, cmap="summer", legend=True
        )
        #    stacked=True, ax=ax
        # )
        ax.set_axisbelow(True)
        ax.grid(axis="y")
        # ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12))
        # ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12))

        # plt.xlabel("Publication year")
        # plt.ylabel("Number of articles")
        # plt.yticks(list(range(0, 25, 5)))
        plt.tight_layout()
        plt.savefig("/tmp/fig_type.svg")
        # plt.show()

    def plot_waffle_type(self):
        data = {"Journal Article": 32, "Conference Paper": 45}
        fig = plt.figure(
            FigureClass=Waffle,
            rows=5,
            values=data,
            colors=("#232066", "#983D3D"),
            legend={
                "loc": "lower center",
                "bbox_to_anchor": (0, -0.4),
                "ncol": len(data),
            },
            icons="book",
            icon_size=18,
            icon_legend=True,
        )
        plt.savefig("/tmp/fig_type.svg")
        # plt.show()

    def plot_continent(self):
        self.__df.groupby(["continent"]).size().plot.pie(
            legend=True,
            autopct="%1.0f%%",
            cmap="YlGn",
            # colors=["red", "green", "blue", "orange", "purple"],
        )
        plt.tight_layout()
        plt.savefig("/tmp/fig_continent.pdf")

    def plot_geo_continent(self):
        fig, ax = plt.subplots(1, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        # print(self.__df.groupby(["continent"]).size().head())
        world = geopandas.read_file(
            geopandas.datasets.get_path("naturalearth_lowres")
        ).dissolve(by="continent", aggfunc="sum")
        publications = [0, np.nan, 16, 39, 20, 2, 0, 0]
        world["publications"] = publications
        world.plot(column="publications", legend=True, ax=ax, cax=cax)
        plt.tight_layout()
        plt.savefig("/tmp/fig_geo_continent.svg")
        # plt.show()

    def plot_publisher(self):
        print(self.__df.groupby(["publisher"]).size().head(10))
        cmap = "summer"
        # cmap = "Wistia"
        to_replace = {"John Wiley": "Others", "MDPI": "Others", "Elsevier": "Others"}
        self.__df["publisher"] = self.__df["publisher"].replace(to_replace=to_replace)
        self.__df.groupby(["year", "publisher"]).size().unstack().plot.bar(
            stacked=True, figsize=(6, 4), cmap=cmap, legend=False
        )
        # handles, labels = plt.gca().get_legend_handles_labels()
        # order = [1,2,0,3]
        # plt.legend([handles[idx] for idx in order],[labels[idx] for idx in order])
        plt.legend(loc="upper left")
        plt.xlabel("")
        plt.ylabel("Studies included in the review")
        plt.yticks(list(range(0, 25, 5)))

        x = [0, 1, 2, 3, 4]
        y = [3203, 5148, 7327, 10053, 10441]

        color = "royalblue"
        axes2 = plt.twinx()
        axes2.plot(x, y, color=color, label="Sine", marker="s", linestyle="dashed")
        axes2.set_ylabel("Records initially identified", color=color)
        axes2.tick_params(axis="y", labelcolor=color)
        axes2.set_ylim(ymin=0)

        plt.tight_layout()

        # plt.show()
        plt.savefig("/tmp/fig_publisher.pdf")

    def plot_keywords(self):
        plt.close("all")
        keywords = np.genfromtxt("search_terms.csv", dtype=str, delimiter="\n")

        pos = {}
        vertical_limit = 20
        step = vertical_limit / (len(keywords[0].split(",")) - 1)
        for i, kw in enumerate(keywords[0].split(",")):
            pos[kw] = (0, i * step)
            # print(i * step)

        step = vertical_limit / (len(keywords[1].split(",")) - 1)
        for i, kw in enumerate(keywords[1].split(",")):
            pos[kw] = (1, i * step)
            # print(i * step)

        step = vertical_limit / (len(keywords[2].split(",")) - 1)
        for i, kw in enumerate(keywords[2].split(",")):
            pos[kw] = (2, i * step)
            # print(i * step)

        G = nx.Graph()
        fig = plt.figure(1, figsize=(8, 4.8))

        options = {"edgecolors": "tab:gray", "node_size": 200, "alpha": 1.0}
        nx.draw_networkx_nodes(
            G,
            nodelist=keywords[0].split(","),
            node_color="tab:blue",
            pos=pos,
            **options
        )
        nx.draw_networkx_nodes(
            G, nodelist=keywords[1].split(","), node_color="tab:red", pos=pos, **options
        )
        nx.draw_networkx_nodes(
            G,
            nodelist=keywords[2].split(","),
            node_color="tab:green",
            pos=pos,
            **options
        )
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)

        edgelist = []
        for k0 in keywords[0].split(","):
            for k1 in keywords[1].split(","):
                edgelist.append((k0, k1))

        for k1 in keywords[1].split(","):
            for k2 in keywords[2].split(","):
                edgelist.append((k1, k2))

        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=edgelist,
            alpha=0.4,
            edge_color="tab:grey",
        )

        # fig, ax = plt.subplots(1, 1, figsize=(6, 1))
        # plt.figure(figsize=(6, 1))
        # plt.figure(figsize=(3, 3))

        # plt.figure(1, figsize=(6, 12))
        # plt.tight_layout()
        # fig, ax = plt.subplots()
        # f, axs = plt.subplots(1, 1, figsize=(15, 1))

        # fig = plt.figure(1, figsize=(2000, 80), dpi=60)

        # plt.show()
        plt.savefig("/tmp/fig_keywords.svg")
