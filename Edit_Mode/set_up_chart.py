import time
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
from utils import (
    create_bar_chart_with_infinite_bars,
    render_markdown,
    create_line_chart_with_infinite_lines,
    create_pie_chart_with_infinite_slices,
    create_variance_comparison_bar_chart,
    create_year_and_month_week_and_day_columns,
    create_choropleth_map,
)
from Edit_Mode.components.positions_component.src.streamlit_component_x import position_selector
from datetime import datetime

# Path to the pages.json file
PAGES_FILE = "pages.json"


def load_pages():
    """Load pages configuration from the JSON file."""
    if os.path.exists(PAGES_FILE):
        with open(PAGES_FILE, "r") as file:
            return json.load(file)
    return []


def save_pages(pages):
    """Save pages configuration to the JSON file."""
    with open(PAGES_FILE, "w") as file:
        json.dump(pages, file, indent=4)


def get_dynamic_page_layout():
    """Dynamically generate a default layout for pages."""
    return [
        ["row1, col1", "row1, col2", "row1, col3"],
        ["row2, col1", "row2, col2", "row2, col3"],
        ["row3, col1", "row3, col2", "row3, col3"],
        ["row4, col1", "row4, col2", "row4, col3"],
        ["row5, col1", "row5, col2"],
        ["full row 6"],
        ["row7, col1", "row7, col2", "row7, col3"],
    ]


def get_available_positions(page_name):
    """Get available positions for the selected page."""
    layout = get_dynamic_page_layout()
    flat_layout = [pos for row in layout for pos in row]
    pages = load_pages()

    used_positions = [
        chart.get("position")
        for page in pages
        if page["title"] == page_name
        for chart in page.get("charts", [])
        if "position" in chart
    ]

    new_positions = []
    for position in used_positions:
        new_positions.extend(position)
    list_options = []

    for pos in flat_layout:
        if pos.upper() not in new_positions:
            list_options.append(pos.upper())
        else:
            list_options.append(f":red[{pos.upper()}]")

    return list_options


def setup():
    """Main function to set up a chart."""
    st.title("Dynamic Chart Setup")

    # Step 1: Select the `.parquet` file
    st.subheader("Step 1: Select Data File")
    data_dir = "./database"

    try:
        files = [f for f in os.listdir(data_dir) if f.endswith(".parquet")]
    except FileNotFoundError:
        st.error(f"The directory '{data_dir}' does not exist.")
        return

    if not files:
        st.warning("No `.parquet` files found in the 'database' directory.")
        return

    selected_file = st.selectbox("Select a `.parquet` file", options=[None] + files)
    if not selected_file:
        st.info("Please select a `.parquet` file to proceed.")
        return

    file_path = os.path.join(data_dir, selected_file)
    df = pd.read_parquet(file_path)
    st.write("### Preview of Selected DataFrame")
    st.dataframe(df.head(5))

    # Step 2: Select the page and container position
    st.subheader("Step 2: Select Page and Position")
    pages = load_pages()
    page_titles = [page["title"] for page in pages]
    selected_page = st.selectbox(
        "Select Page to Publish Chart",
        options=page_titles,
        index=page_titles.index(st.session_state["last_page_selected"]),
    )
    if selected_page:
        available_positions = get_available_positions(selected_page)
        if not available_positions:
            st.warning(
                "No available positions on this page. Please remove an existing chart or select a different page."
            )
            return
        selected_position = position_selector(positions=available_positions)
        if selected_position and [pos for pos in selected_position if "red" in pos]:
            st.info(
                "This position is already occupied. Please select a different position."
            )
            return
        if not selected_position:
            st.info("Please select a position to proceed.")
            return
    else:
        st.info("Please select a page to proceed.")
        return

    # Step 3: Configure the chart
    st.subheader("Step 3: Configure Chart")
    chart_title = st.text_input("Enter Chart Title")

    # Define required fields for each chart type
    chart_requirements = {
        "Bar Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Choropleth Map": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Slicer Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Line Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 1},
        "Pie Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Scatter Plot": {"Dimensions": 1, "Measures": 2, "Date Fields": 0},
        "Histogram": {"Dimensions": 0, "Measures": 1, "Date Fields": 0},
        "Variance Comparison": {"Dimensions": 1, "Measures": 1, "Date Fields": 1},
    }

    requirements = chart_requirements.get(st.session_state["chart_to_configure"], {})
    available_dimensions = df.select_dtypes(
        exclude=["number", "datetime"]
    ).columns.tolist()
    available_measures = df.select_dtypes(include=["number"]).columns.tolist()
    available_date_fields = df.select_dtypes(include=["datetime"]).columns.tolist()
    dimension = None
    if st.session_state["chart_to_configure"] != "Variance Comparison":
        dimension = st.selectbox("Select Dimension", available_dimensions)
    dimensions = st.multiselect("Select Filters", available_dimensions)
    display_filters = False
    if st.session_state.chart_to_configure == "Slicer Chart":    
        display_filters = st.checkbox("Display filters in table", key=f"Slicer tool", help="Use for display columns in table for each filter")
    measures = st.multiselect("Select Measures", available_measures)
    date_fields = st.multiselect("Select Date Fields", available_date_fields)

    if len(measures) < requirements.get("Measures", 0):
        st.warning(
            f"This chart requires at least {requirements['Measures']} measure(s)."
        )
        return

    if len(date_fields) < requirements.get("Date Fields", 0):
        st.warning(
            f"This chart requires at least {requirements['Date Fields']} date field(s)."
        )
        return

    default_dynamic_measure = measures[0]

    if st.session_state["chart_to_configure"] != "Variance Comparison":
        st.subheader("Step 4: Data Preview")

    if st.session_state["chart_to_configure"] == "Slicer Chart":
        if dimension not in dimensions:
            dimensions.append(dimension)
        df = df.groupby(dimensions).agg({measures[0]: "sum"}).reset_index()
    elif st.session_state["chart_to_configure"] != "Variance Comparison":
        if dimension not in dimensions:
            dimensions.append(dimension)
        df = df.groupby(dimension)[measures[0]].sum().reset_index()
        st.dataframe(df, use_container_width=True, hide_index=True)
    elif st.session_state["chart_to_configure"] == "Variance Comparison":
        create_year_and_month_week_and_day_columns(df, date_fields[0])
        this_year = df["Year"].max()
        total_this_year = df[(df["Year"] == this_year)][measures[0]].sum()
        total_last_year = df[(df["Year"] == this_year - 1)][measures[0]].sum()
    # Step 6: Preview the chart
    invert = False
    st.subheader(
        "Step 5: Chart Preview"
        if st.session_state["chart_to_configure"] != "Variance Comparison"
        else "Step 4: Chart Preview"
    )
    if (
        st.session_state["chart_to_configure"] == "Line Chart"
        or st.session_state["chart_to_configure"] == "Bar Chart"
    ):
        invert = st.toggle("Invert chart")
    if st.session_state["chart_to_configure"] != "Variance Comparison":
        chart_data = {
            "x": df[dimension],
            "y": df[measures[0]],
        }

        if invert:
            chart_data = {
                "x": df[measures[0]],
                "y": df[dimension],
            }

    if st.session_state["chart_to_configure"] == "Bar Chart":
        fig = create_bar_chart_with_infinite_bars(
            data={
                "bars": [
                    {
                        **chart_data,
                    },
                ],
            },
            xaxis_title=measures[0] if invert else dimension,
            yaxis_title=dimension if invert else measures[0],
            orientation="h" if invert else "v",
            text_anotation="Preview example",
        )
        st.plotly_chart(fig)
    elif st.session_state["chart_to_configure"] == "Variance Comparison":
        fig = create_variance_comparison_bar_chart(
            total_this_year=float(total_this_year),
            total_prior_year=float(total_last_year),
            xaxis_title=measures[0],
            prior_year=this_year - 1,
            this_year=this_year,
            additional_info=None,
        )
        st.plotly_chart(fig)
    elif st.session_state["chart_to_configure"] == "Line Chart":
        fig = create_line_chart_with_infinite_lines(
            data={
                "lines": [
                    {
                        **chart_data,
                    },
                ],
            },
            xaxis_title=dimension,
            yaxis_title=measures[0],
            annotation="Preview example",
        )
        st.plotly_chart(fig)

    elif st.session_state["chart_to_configure"] == "Slicer Chart":
        st.dataframe(df, use_container_width=True, hide_index=True)

    elif st.session_state["chart_to_configure"] == "Pie Chart":
        chart_data = {
            "labels": df[dimension],
            "values": df[measures[0]],
        }
        fig = create_pie_chart_with_infinite_slices(
            data={
                "slices": [
                    {
                        **chart_data,
                    },
                ],
            },
            annotation="Preview example",
        )
        st.plotly_chart(fig)
    elif st.session_state["chart_to_configure"] == "Choropleth Map":
        fig = create_choropleth_map(df, measures[0], dimension, chart_title)
        st.plotly_chart(fig)

    else:
        st.info("No Preview Available")
    # Step 6: Save Chart Configuration
    if st.button("Save Chart Configuration", use_container_width=True):

        chart_config = {
            "chart_name": chart_title,
            "type": st.session_state["chart_to_configure"],
            "dimension": dimensions,
            "main_dimension": dimension,
            "measure": measures,
            "date_column": date_fields,
            "filter_dimensions": dimensions,
            "dynamic_measures": measures,
            "default_dynamic_measure": default_dynamic_measure,
            "file_path": file_path,
            "position": selected_position,
            "invert": invert,
            "display_filters": display_filters,
        }
        import uuid

        for page in pages:
            if page["title"] == selected_page:
                if "charts" not in page:
                    page["charts"] = []
                chart_id = uuid.uuid4().hex
                chart_config["chart_id"] = chart_id
                page["charts"].append(chart_config)
                break

        save_pages(pages)
        st.session_state["selected_chart_for_rendering"] = selected_page
        st.success(f"Chart '{chart_title}' has been configured and saved!")
        time.sleep(3)
        st.switch_page("./nav_bar.py")


if __name__ == "__main__":
    setup()
