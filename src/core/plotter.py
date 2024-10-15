import logging
import tempfile
from collections import Counter

import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import pycountry_convert as pc
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle
from shapely.geometry import Point

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

    def count_clean_countries(self, country_list: list):
        # Clean the list and count the ocurrencies of every country and ignore the empty ones
        new_list = []

        for i in range(len(country_list)):
            if country_list[i] is not None:
                new_list.append(country_list[i])

        country_count = Counter(new_list)

        # Order contries using frequency
        sorted_countries = sorted(country_count.items(), key=lambda x: x[1], reverse=True)
        countries = [item[0] for item in sorted_countries]
        counts = [item[1] for item in sorted_countries]

        return countries, counts, sorted_countries

    def plot_type(self, document_types: list):
        labels, sizes = zip(*document_types, strict=True)

        fig, ax = plt.subplots()

        colors = plt.cm.summer(np.linspace(0, 1, len(document_types)))

        # pie chart
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90, pctdistance=0.5, labeldistance=0.7
        )

        # Adjust text position
        for autotext in autotexts:
            autotext.set(size=10, color="white", weight="bold")

        # To form an sphere and not a ellipse
        ax.axis("equal")

        ax.set_title("Distribution of Publication Types")
        plt.tight_layout()
        plt.show()

    def show_country_bar_diagram(self, country_list: list):
        countries, counts, _ = self.count_clean_countries(country_list)

        # Create the graph
        plt.figure(figsize=(14, 8))
        bars = plt.bar(countries, counts, color="skyblue")

        # Tags of the bars
        for bar in bars:
            yval = bar.get_height()
            aux = bar.get_x() + bar.get_width() / 2
            plt.text(aux, yval + 0.1, str(int(yval)), ha="center", va="bottom", fontsize=10, fontweight="bold")

        plt.ylabel("Number of Occurrences")
        plt.xlabel("Countries")
        plt.title("Country Occurrences")

        plt.xticks(rotation=45, ha="right")
        plt.grid(axis="y", linestyle="--", alpha=0.7)

        plt.tight_layout()
        plt.show()

    def plot_bar_type(self, document_years: list):
        df = pd.DataFrame(document_years, columns=["year", "number_of_articles"])

        fig, ax = plt.subplots()

        df.set_index("year")["number_of_articles"].plot(kind="bar", ax=ax)

        ax.set_axisbelow(True)
        ax.grid(axis="y")
        ax.legend(["Number of articles"], ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12))

        plt.xlabel("Publication year")
        plt.ylabel("Number of articles")
        plt.xticks(rotation=0)
        plt.yticks(list(range(0, 500, 50)))
        plt.tight_layout()

        plt.show()

    def show_country_map(self, country_list: list):
        countries, counts, sorted_countries = self.count_clean_countries(country_list)

        # Load the world shapefile
        shapefile_path = "src/files/ne_110m_admin_0_countries.shp"
        world = gpd.read_file(shapefile_path)
        world["SOVEREIGNT"] = world["SOVEREIGNT"].str.upper()

        # Create frequency map
        frequency_map = {country.upper(): count for country, count in zip(countries, counts, strict=False)}
        if "UNITED STATES" in frequency_map:
            frequency_map["UNITED STATES OF AMERICA"] = frequency_map["UNITED STATES"]

        world["frequency"] = world["SOVEREIGNT"].map(frequency_map).fillna(0)

        fig, ax = plt.subplots(1, 1, figsize=(20, 15), facecolor="#F0F0F0")

        # Create a custom colormap
        colors = ["#FFF5EB", "#FEE6CE", "#FDD0A2", "#FDAE6B", "#FD8D3C", "#F16913", "#D94801", "#A63603", "#7F2704"]
        n_bins = len(colors)
        cmap = LinearSegmentedColormap.from_list("custom_cmap", colors, N=n_bins)

        # Normalize the frequency data
        vmin, vmax = 0, world["frequency"].max()
        norm = plt.Normalize(vmin=vmin, vmax=vmax)

        world.plot(
            column="frequency",
            ax=ax,
            cmap=cmap,
            norm=norm,
            legend=True,
            legend_kwds={
                "label": "Number of Documents",
                "orientation": "horizontal",
                "shrink": 0.6,
                "aspect": 20,
                "pad": 0.08,
            },
            missing_kwds={"color": "lightgrey"},
        )

        # Add country boundaries
        world.boundary.plot(ax=ax, linewidth=0.2, color="black")

        # Add text for countries with data
        for _idx, row in world.iterrows():
            if row["frequency"] > 0:
                centroid = row["geometry"].centroid
                if row["SOVEREIGNT"] == "FRANCE":
                    centroid = Point(1.5, 47)
                elif row["SOVEREIGNT"] == "UNITED KINGDOM":
                    centroid = Point(-1, 53)
                elif row["SOVEREIGNT"] == "UNITED STATES OF AMERICA":
                    centroid = Point(-100, 40)
                elif row["SOVEREIGNT"] == "CANADA":
                    centroid = Point(-110, 60)
                elif row["SOVEREIGNT"] == "NORWAY":
                    centroid = Point(9, 61)
                elif row["SOVEREIGNT"] == "MALAYSIA":
                    centroid = Point(102, 4)
                elif row["SOVEREIGNT"] == "INDONESIA":
                    centroid = Point(113, -1)
                elif row["SOVEREIGNT"] == "MOROCCO":
                    centroid = Point(-6, 32)

                text = ax.text(
                    centroid.x,
                    centroid.y,
                    str(int(row["frequency"])),
                    fontsize=8,
                    ha="center",
                    va="center",
                    color="black",
                )
                text.set_path_effects([path_effects.Stroke(linewidth=2, foreground="white"), path_effects.Normal()])

        # Create a table with the top 10 countries
        top_10 = sorted_countries[:10]
        table_data = [(country, freq) for country, freq in top_10]

        table = ax.table(
            cellText=table_data,
            colLabels=["Country", "Documents"],
            loc="center",
            cellLoc="center",
            bbox=[-0.3, 0.3, 0.2, 0.5],
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        # Style the table
        for (row, _col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(weight="bold", color="white")
                cell.set_facecolor("#4472C4")
            else:
                cell.set_facecolor("#E6F2FF" if row % 2 == 0 else "white")

        plt.title("Global Distribution of Documents by Country", fontsize=20, pad=20)
        ax.axis("off")

        plt.tight_layout()
        plt.show()

    def plot_continent(self):
        self.__df.groupby(["continent"]).size().plot.pie(
            legend=True,
            autopct="%1.0f%%",
            cmap="YlGn",
            # colors=["red", "green", "blue", "orange", "purple"],
        )
        plt.tight_layout()
        plt.savefig(f"{tempfile.gettempdir()}/fig_continent.pdf")

    def get_continent(self, country_name):
        country_alpha2 = pc.country_name_to_country_alpha2(country_name)
        country_continent_code = pc.country_alpha2_to_continent_code(country_alpha2)
        country_continent_name = pc.convert_continent_code_to_continent_name(country_continent_code)

        return country_continent_name

    def plot_geo_continent(self, documents_per_country: list):
        # Count occurrences of each continent
        continent_counts = {}
        for country_name in documents_per_country:
            if country_name:
                continent = self.get_continent(country_name)
                if continent:
                    continent_counts[continent] = continent_counts.get(continent, 0) + 1

        documents_per_continent = continent_counts

        world = gpd.read_file("src/files/ne_110m_admin_0_countries.shp")

        fig, ax = plt.subplots(figsize=(15, 10))

        # Define a color map
        cmap = plt.cm.Set3
        continents = world["CONTINENT"].unique()
        color_dict = dict(zip(continents, [cmap(i) for i in range(len(continents))], strict=False))

        # Plot the continents
        for continent, data in world.groupby("CONTINENT"):
            color = color_dict[continent]
            data.plot(ax=ax, color=color, label=continent)

        # Define continent centroids (approximate)
        centroids = {
            "North America": (-100, 45),
            "South America": (-60, -15),
            "Europe": (15, 50),
            "Africa": (20, 0),
            "Asia": (80, 35),
            "Oceania": (130, -25),
            "Antarctica": (0, -90),
        }

        # Add custom numbers to each continent
        for continent, (x, y) in centroids.items():
            if continent in documents_per_continent:
                number = documents_per_continent[continent]
                ax.add_patch(Circle((x, y), 5, facecolor="white", edgecolor="black", zorder=2))
                ax.text(x, y, str(number), ha="center", va="center", fontweight="bold", zorder=3)

        ax.set_title("How much documents per continent", fontsize=16)
        ax.axis("off")

        # Create a custom legend
        legend_element = [
            plt.Rectangle(
                (0, 0),
                1,
                1,
                facecolor=color_dict[c],
                edgecolor="none",
                label=f"{c} ({documents_per_continent.get(c, 'N/A')})",
            )
            for c in continents
        ]

        ax.legend(handles=legend_element, loc="lower center", bbox_to_anchor=(0.5, -0.05), ncol=4)

        plt.tight_layout()

        plt.show()

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
