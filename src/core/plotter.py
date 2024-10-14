import logging
import tempfile

import geopandas
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

LOGGER = logging.getLogger("systematic")


class Plotter:
    # chose a colormap
    # https://matplotlib.org/2.0.2/users/colormaps.html

    def defining_spacing(self, param_list: list):
        if len(param_list) < 6:
            spacing_set = 18
        elif len(param_list) < 9:
            spacing_set = 10
        else:
            spacing_set = 5

        return spacing_set

    def plot_bar_type(self):
        fig, ax = plt.subplots()
        self.__df.groupby(["year", "sub_type"]).size().unstack().plot.bar(stacked=True, ax=ax)
        #    stacked=True, ax=ax
        # )
        ax.set_axisbelow(True)
        ax.grid(axis="y")
        ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12))

        plt.xlabel("Publication year")
        plt.ylabel("Number of articles")
        plt.yticks(list(range(0, 25, 5)))
        plt.tight_layout()
        plt.savefig(f"{tempfile.gettempdir()}/fig_type.svg")
        # plt.show()

    def plot_type(self):
        fig, ax = plt.subplots()
        # self.__df.groupby(["year", "sub_type"]).size().unstack().plot.bar(
        #    stacked=True, ax=ax
        # )
        # self.__df.groupby(["sub_type"]).size().plot.bar(ax=ax)
        self.__df.groupby(["sub_type"]).size().plot.pie(ax=ax, cmap="summer", legend=True)
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
        plt.savefig(f"{tempfile.gettempdir()}/fig_type.svg")
        # plt.show()

    def plot_continent(self):
        self.__df.groupby(["continent"]).size().plot.pie(
            legend=True,
            autopct="%1.0f%%",
            cmap="YlGn",
            # colors=["red", "green", "blue", "orange", "purple"],
        )
        plt.tight_layout()
        plt.savefig(f"{tempfile.gettempdir()}/fig_continent.pdf")

    def plot_geo_continent(self):
        fig, ax = plt.subplots(1, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        # print(self.__df.groupby(["continent"]).size().head())
        world = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres")).dissolve(
            by="continent", aggfunc="sum"
        )
        publications = [0, np.nan, 16, 39, 20, 2, 0, 0]
        world["publications"] = publications
        world.plot(column="publications", legend=True, ax=ax, cax=cax)
        plt.tight_layout()
        plt.savefig(f"{tempfile.gettempdir()}/fig_geo_continent.svg")
        # plt.show()

    def plot_publisher(self):
        print(self.__df.groupby(["publisher"]).size().head(10))
        cmap = "summer"
        # cmap = "Wistia"
        to_replace = {
            "John Wiley": "Others",
            "MDPI": "Others",
            "Elsevier": "Others",
        }
        self.__df["publisher"] = self.__df["publisher"].replace(to_replace=to_replace)
        self.__df.groupby(["year", "publisher"]).size().unstack().plot.bar(
            stacked=True, figsize=(6, 4), cmap=cmap, legend=False
        )
        # handles, labels = plt.gca().get_legend_handles_labels()
        # order = [1,2,0,3]
        # plt.legend([handles[idx] for idx in order],
        # [labels[idx] for idx in order])
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
        plt.savefig(f"{tempfile.gettempdir()}/fig_publisher.pdf")

    def relations_diagram(self, set_1: list, set_2: list, set_3: list):
        relation_graph = nx.Graph()

        # Agreggate the nodes of all the set
        relation_graph.add_nodes_from(set_1)
        relation_graph.add_nodes_from(set_2)
        relation_graph.add_nodes_from(set_3)

        # Connect the nodes
        for node1 in set_1:
            for node2 in set_2:
                relation_graph.add_edge(node1, node2)

        for node2 in set_2:
            for node3 in set_3:
                relation_graph.add_edge(node2, node3)

        spacing_set1 = self.defining_spacing(set_1)
        spacing_set2 = self.defining_spacing(set_2)
        spacing_set3 = self.defining_spacing(set_3)

        # Assign the position of every node

        pos = {}

        for i, node in enumerate(set_1):
            pos[node] = (0, i * spacing_set1)

        for i, node in enumerate(set_2):
            pos[node] = (1, i * spacing_set2)

        for i, node in enumerate(set_3):
            pos[node] = (2, i * spacing_set3)

        # Assign the color of every set (column in the graph)

        colors_1 = ["lightblue"] * len(set_1)  # Colores para el primer set
        colors_2 = ["lightgreen"] * len(set_2)  # Colores para el segundo set
        colors_3 = ["mediumorchid"] * len(set_3)  # Colores morados para el tercer set

        node_colors = colors_1 + colors_2 + colors_3

        # Generate colors for the lines that join set values

        color_palette = list(mcolors.TABLEAU_COLORS.values())
        edge_colors = np.resize(color_palette, len(relation_graph.edges()))

        # Draw the graph
        plt.figure(figsize=(12, 8))

        draw_params = {
            "with_labels": False,
            "node_size": 1000,
            "node_color": node_colors,
            "font_size": 10,
            "font_weight": "bold",
            "edge_color": edge_colors,
            "width": 2,
            "alpha": 0.8,
        }

        nx.draw(relation_graph, pos, **draw_params)

        # Draw the tag of every node
        for node, (x, y) in pos.items():
            plt.text(x, y, node, fontsize=10, fontweight="bold", ha="center", va="top", color="black")

        # Add column names
        column_names = ["Topic", "Action", "Dimension"]
        for i, set_name in enumerate(column_names):
            plt.text(
                i,
                max(pos.values(), key=lambda x: x[1])[1] + 4,
                set_name,
                fontsize=14,
                fontweight="bold",
                ha="center",
                va="bottom",
            )

        plt.axis("off")
        plt.show()
