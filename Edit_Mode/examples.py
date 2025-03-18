"""
Este módulo eu usei para colocar exemplos de todos os gráficos que ficam disponíveis na aplicação.
Aqui fica todos aqueles gráficos que são mostrados no portfólio.

A ideia é instanciar a classe Examples e chamar os métodos que geram os gráficos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import create_choropleth_map, create_variance_comparison_bar_chart

class Examples:

    def __init__(self, category_df, df):
        self.category_df = category_df
        self.df = df

    def create_variance_comparison_bar_chart(self):
        fig = create_variance_comparison_bar_chart(total_this_year=100, total_prior_year=80, xaxis_title="Year",prior_year=2019, this_year=2020)
        st.plotly_chart(fig)

    def bar_chart(self):
        fig = px.bar(self.category_df, x="Category", y="Values", title="Bar Chart")
        st.plotly_chart(fig)

    def slicer_chart(self):
        st.dataframe(self.df, use_container_width=True, hide_index=True)

    def line_chart(self):
        fig = px.line(self.df, title="Line Chart", labels={"index": "Index", "value": "Value"})
        st.plotly_chart(fig)


    def pie_chart(self):
        fig = px.pie(self.category_df, names="Category", values="Values", title="Pie Chart")
        st.plotly_chart(fig)


    def scatter_plot(self):
        fig = px.scatter(
            self.df, x="A", y="B", title="Scatter Plot", labels={"A": "X-axis", "B": "Y-axis"}
        )
        st.plotly_chart(fig)

    def histogram(self):
        fig = px.histogram(self.df, x="A", title="Histogram", labels={"A": "Values"})
        st.plotly_chart(fig)


    def box_plot(self):
        fig = px.box(self.df, title="Box Plot")
        st.plotly_chart(fig)


    def heatmap(self):
        fig = go.Figure(data=go.Heatmap(z=self.df.corr().values, x=self.df.columns, y=self.df.columns))
        fig.update_layout(title="Heatmap", xaxis_title="Features", yaxis_title="Features")
        st.plotly_chart(fig)


    def area_chart(self):
        fig = px.area(self.df, title="Area Chart")
        st.plotly_chart(fig)

    def choropleth_map(self):
        df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/2014_world_gdp_with_codes.csv")
        fig = create_choropleth_map(
            df,
            measure="GDP (BILLIONS)",
            location_column="COUNTRY",
        )
        st.plotly_chart(fig)

    def radar_chart(self):
        categories = ["A", "B", "C"]
        values = self.df.mean().values.tolist()
        fig = go.Figure()
        fig.add_trace(
            go.Scatterpolar(r=values, theta=categories, fill="toself", name="Average")
        )
        fig.update_layout(title="Radar Chart")
        st.plotly_chart(fig)


    def bubble_chart(self):
        # Ensure 'C' values are non-negative for the 'size' parameter
        self.df["C"] = self.df["C"].abs()  # Take the absolute value of column 'C'

        # Create a bubble chart using non-negative sizes
        fig = px.scatter(
            self.df,
            x="A",
            y="B",
            size="C",  # Size must be non-negative
            title="Bubble Chart",
            labels={"A": "X-axis", "B": "Y-axis", "C": "Size"},
        )
        st.plotly_chart(fig)


    def donut_chart(self):
        fig = px.pie(
            self.category_df, names="Category", values="Values", hole=0.4, title="Donut Chart"
        )
        st.plotly_chart(fig)


    def candlestick_chart(self):
        random_data = pd.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=50),
                "Open": np.random.rand(50),
                "High": np.random.rand(50) + 1,
                "Low": np.random.rand(50) - 1,
                "Close": np.random.rand(50),
            }
        )
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=random_data["Date"],
                    open=random_data["Open"],
                    high=random_data["High"],
                    low=random_data["Low"],
                    close=random_data["Close"],
                )
            ]
        )
        fig.update_layout(title="Candlestick Chart")
        st.plotly_chart(fig)


    def violin_plot(self):
        fig = px.violin(self.df, y="A", title="Violin Plot")
        st.plotly_chart(fig)


    def density_contour(self):
        fig = px.density_contour(self.df, x="A", y="B", title="Density Contour")
        st.plotly_chart(fig)


    def line_area_combined(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=self.df.index, y=self.df["A"], mode="lines", name="Line"))
        fig.add_trace(go.Scatter(x=self.df.index, y=self.df["B"], fill="tozeroy", name="Area"))
        fig.update_layout(title="Line and Area Combined Chart")
        st.plotly_chart(fig)


    def scatter_3d(self):
        fig = px.scatter_3d(self.df, x="A", y="B", z="C", title="3D Scatter Plot")
        st.plotly_chart(fig)


    def bar_stacked(self):
        fig = px.bar(self.df, title="Stacked Bar Chart", barmode="stack")
        st.plotly_chart(fig)


    def treemap(self):
        fig = px.treemap(self.category_df, path=["Category"], values="Values", title="Treemap")
        st.plotly_chart(fig)


    def sunburst(self):
        fig = px.sunburst(
            self.category_df, path=["Category"], values="Values", title="Sunburst Chart"
        )
        st.plotly_chart(fig)
