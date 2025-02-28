import time
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import os
import pages_data
from utils import (
    create_bar_chart_with_infinite_bars,
    render_markdown,
    create_rows,
    create_bar_chart_with_filters,
    create_year_and_month_week_and_day_columns,
    render_chart_with_base_type_of_chart,
    create_variance_comparison_bar_chart,
    create_filters,
create_choropleth_map)
import set_up_chart


# Sample dataset for charts
df = pd.DataFrame(np.random.randn(50, 3), columns=["A", "B", "C"])
category_df = pd.DataFrame({"Category": ["A", "B", "C"], "Values": [25, 35, 40]})


def create_page(pages):
    """Handles creating a new page."""
    new_page_name = st.text_input("New Page Name")
    with_title = st.checkbox("Show with title")

    if st.button("Create Page", use_container_width=True):
        if new_page_name:
            if any(p["title"] == new_page_name for p in pages):
                st.error("Page with this name already exists.")
            else:
                pages_data.add_page({"title": new_page_name, "charts": [], "with_title": with_title})
                st.success(f"Page '{new_page_name}' created.")
                time.sleep(2)
                st.rerun()  # Refresh the UI
        else:
            st.error("Please provide a page name.")


def edit_page(pages):
    """Handles editing an existing page."""
    if pages:
        page_name = st.sidebar.selectbox(
            "Select Page to Add Chart", [p["title"] for p in pages],
        )
        if page_name:
            st.sidebar.write(f"Adding Chart to Page: {page_name}")
            set_up_chart.main()
    else:
        st.sidebar.warning("No pages available to Add Charts.")


def delete_page(pages):
    """Handles deleting a page."""
    if pages:
        page_name = st.selectbox(
            "Select Page to Delete", [p["title"] for p in pages],
            index=0,
            
        )
        confirm_delete = st.checkbox("Confirm delete")
        if st.button("Delete Page", use_container_width=True):
            if confirm_delete:
                pages = [p for p in pages if p["title"] != page_name]
                pages_data.save_pages(pages)
                st.success(f"Page '{page_name}' deleted.")
                st.rerun()  # Refresh the UI
            else:
                st.error("Please confirm the deletion.")
    else:
        st.warning("No pages available to delete.")


def rename_page(pages):
    """Handles renaming a page."""
    if pages:
        page_name = st.selectbox(
            "Select Page to Rename", [p["title"] for p in pages]
        )
        new_page_name = st.text_input("Enter New Page Name")
        if st.button("Rename Page", use_container_width=True):
            if new_page_name:
                if any(p["title"] == new_page_name for p in pages):
                    st.error("Page with this name already exists.")
                else:
                    for page in pages:
                        if page["title"] == page_name:
                            page["title"] = new_page_name
                            pages_data.save_pages(pages)
                            st.success(f"Page renamed to '{new_page_name}'.")
                            st.rerun()  # Refresh the UI
            else:
                st.error("Please provide a new name.")
    else:
        st.warning("No pages available to rename.")



@st.dialog(title="Add Chart", width="large")
def cadastre_form():
    set_up_chart.setup()

def delete_chart(pages, selected_page, page):
    
    selected_chart = st.selectbox(label = "Select Chart", options = page.get("charts"), index=0, format_func=lambda x: x["chart_name"])
    if st.button("Delete Chart", use_container_width=True, disabled=selected_chart is None):
        page["charts"] = [chart for chart in page["charts"] if chart["chart_name"] != selected_chart["chart_name"]]
        pages = [
            p if p["title"] != selected_page else page for p in pages
        ]
        set_up_chart.save_pages(pages)
        st.success(f"Chart {selected_chart['chart_name']} deleted.")
        time.sleep(2)
        st.rerun()
def view_pages(pages):
    """Handles displaying and rendering pages."""
    st.sidebar.subheader("View Pages")
    if pages:
        container = False
        if st.sidebar.toggle("Edit Mode :material/edit:", False):
            col1, col2 = st.columns([1, 4])
            with col1:
                with st.popover(":green[Add Chart]", use_container_width=True):
                    portfolio_page()
            with col2:
                with st.popover(":red[Delete Chart]", use_container_width=True):
                    container = st.container()
        selected_page = st.sidebar.selectbox(
            "Select Page", [page["title"] for page in pages], index=0
        )
        st.session_state["last_page_selected"] = selected_page
        page = next((p for p in pages if p["title"] == selected_page), None)
        if not container is False:
            with container:
                delete_chart(pages, selected_page, page)
        if page:
            if page.get("with_title"):
                st.title(page["title"], anchor=False)
            if not page.get("charts"):
                st.info("This page has no charts yet.")
            else:
                rows = create_rows(page.get("charts"))
                datasets = {}
                for chart in page.get("charts", []):
                    if chart.get("file_path") not in datasets.keys():
                        datasets[chart.get("file_path")] = chart.get("date_column")
                rows = {k: v for k, v in rows.items() if isinstance(k, int) }
                rows = {k: v for k, v in sorted(rows.items())}
                ordened_values = list(dict(sorted(rows.items())).values())

                for chart in page.get("charts", []):
                    for value in ordened_values:
                        for row in value:
                            if len(row) > 1 and chart["chart_id"] == row[1]:
                                with row[0]:
                                    render_chart_with_base_type_of_chart(
                                        chart,
                                    )


        else:
            st.info("No pages available.")
    else:
        st.sidebar.info("No pages available. Please create one in Setup Mode.")

# Chart functions
def bar_chart():
    fig = px.bar(category_df, x="Category", y="Values", title="Bar Chart")
    st.plotly_chart(fig)

def slicer_chart():
    st.dataframe(df, use_container_width=True, hide_index=True)

def line_chart():
    fig = px.line(df, title="Line Chart", labels={"index": "Index", "value": "Value"})
    st.plotly_chart(fig)


def pie_chart():
    fig = px.pie(category_df, names="Category", values="Values", title="Pie Chart")
    st.plotly_chart(fig)


def scatter_plot():
    fig = px.scatter(
        df, x="A", y="B", title="Scatter Plot", labels={"A": "X-axis", "B": "Y-axis"}
    )
    st.plotly_chart(fig)


def histogram():
    fig = px.histogram(df, x="A", title="Histogram", labels={"A": "Values"})
    st.plotly_chart(fig)


def box_plot():
    fig = px.box(df, title="Box Plot")
    st.plotly_chart(fig)


def heatmap():
    fig = go.Figure(data=go.Heatmap(z=df.corr().values, x=df.columns, y=df.columns))
    fig.update_layout(title="Heatmap", xaxis_title="Features", yaxis_title="Features")
    st.plotly_chart(fig)


def area_chart():
    fig = px.area(df, title="Area Chart")
    st.plotly_chart(fig)

def choropleth_map():
    df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/2014_world_gdp_with_codes.csv")
    fig = create_choropleth_map(
        df,
        measure="GDP (BILLIONS)",
        location_column="COUNTRY",
        title="Choropleth Map",
    )
    st.plotly_chart(fig)

def radar_chart():
    categories = ["A", "B", "C"]
    values = df.mean().values.tolist()
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(r=values, theta=categories, fill="toself", name="Average")
    )
    fig.update_layout(title="Radar Chart")
    st.plotly_chart(fig)


def bubble_chart():
    # Ensure 'C' values are non-negative for the 'size' parameter
    df["C"] = df["C"].abs()  # Take the absolute value of column 'C'

    # Create a bubble chart using non-negative sizes
    fig = px.scatter(
        df,
        x="A",
        y="B",
        size="C",  # Size must be non-negative
        title="Bubble Chart",
        labels={"A": "X-axis", "B": "Y-axis", "C": "Size"},
    )
    st.plotly_chart(fig)


def donut_chart():
    fig = px.pie(
        category_df, names="Category", values="Values", hole=0.4, title="Donut Chart"
    )
    st.plotly_chart(fig)


def candlestick_chart():
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


def violin_plot():
    fig = px.violin(df, y="A", title="Violin Plot")
    st.plotly_chart(fig)


def density_contour():
    fig = px.density_contour(df, x="A", y="B", title="Density Contour")
    st.plotly_chart(fig)


def line_area_combined():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["A"], mode="lines", name="Line"))
    fig.add_trace(go.Scatter(x=df.index, y=df["B"], fill="tozeroy", name="Area"))
    fig.update_layout(title="Line and Area Combined Chart")
    st.plotly_chart(fig)


def scatter_3d():
    fig = px.scatter_3d(df, x="A", y="B", z="C", title="3D Scatter Plot")
    st.plotly_chart(fig)


def bar_stacked():
    fig = px.bar(df, title="Stacked Bar Chart", barmode="stack")
    st.plotly_chart(fig)


def treemap():
    fig = px.treemap(category_df, path=["Category"], values="Values", title="Treemap")
    st.plotly_chart(fig)


def sunburst():
    fig = px.sunburst(
        category_df, path=["Category"], values="Values", title="Sunburst Chart"
    )
    st.plotly_chart(fig)


# Portfolio Page
def portfolio_page():
    """Displays all the chart templates with sample data in a 3-charts-per-row layout and allows adding charts."""
    st.write("## Portfolio Page")
    st.write("Explore all available chart templates populated with sample data.")

    # Chart requirements: Define required fields for each chart
    chart_requirements = {
        "Bar Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Slicer Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 1},
        "Choropleth Map": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Line Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 1},
        "Pie Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Scatter Plot": {"Dimensions": 1, "Measures": 2, "Date Fields": 0},
        "Histogram": {"Dimensions": 0, "Measures": 1, "Date Fields": 0},
        "Box Plot": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Heatmap": {"Dimensions": 2, "Measures": 1, "Date Fields": 0},
        "Area Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 1},
        "Radar Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Bubble Chart": {"Dimensions": 1, "Measures": 2, "Date Fields": 0},
        "Donut Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Candlestick Chart": {
            "Dimensions": 1,
            "Measures": 4,
            "Date Fields": 1,
        },  # Open, High, Low, Close
        "Violin Plot": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Density Contour": {"Dimensions": 2, "Measures": 0, "Date Fields": 0},
        "Line and Area Combined Chart": {
            "Dimensions": 1,
            "Measures": 2,
            "Date Fields": 1,
        },
        "3D Scatter Plot": {"Dimensions": 1, "Measures": 3, "Date Fields": 0},
        "Stacked Bar Chart": {"Dimensions": 1, "Measures": 2, "Date Fields": 0},
        "Treemap": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
        "Sunburst Chart": {"Dimensions": 1, "Measures": 1, "Date Fields": 0},
    }

    # Helper function to render a single chart with an "Add" button
    def render_chart_with_add_button(chart_function, title):
        with st.container():  # Create a container for the chart and button
            st.write(f"### {title}")

            # Display field requirements below the chart title
            requirements = chart_requirements.get(title, {})
            if requirements:
                requirements_text = ", ".join(
                    f"{quantity} {field_type}"
                    for field_type, quantity in requirements.items()
                    if quantity > 0  # Only show fields with non-zero requirements
                )
                st.write(f"**Field Requirements:** {requirements_text}")
            else:
                st.write("**Field Requirements:** Not specified")
            if title == "Variance Comparison":
                st.plotly_chart(chart_function(100,80, xaxis_title=title, title=title, prior_year=2019, this_year=2020))
            else:
                chart_function()  # Render the chart

            # Add button below each chart
            if st.button(f"Add '{title}'", key=f"add_{title}"):
                st.session_state.configure_chart = True
                st.session_state.chart_to_configure = title
                cadastre_form()
                # st.rerun()

    # Group charts into rows of 3
    chart_functions = [
        ("Bar Chart", bar_chart),
        ("Variance Comparison", create_variance_comparison_bar_chart),
        ("Slicer Chart", slicer_chart),
        ("Choropleth Map", choropleth_map),
        ("Line Chart", line_chart),
        ("Pie Chart", pie_chart),
        ("Scatter Plot", scatter_plot),
        ("Histogram", histogram),
        ("Box Plot", box_plot),
        ("Heatmap", heatmap),
        ("Area Chart", area_chart),
        ("Radar Chart", radar_chart),
        ("Bubble Chart", bubble_chart),
        ("Donut Chart", donut_chart),
        ("Candlestick Chart", candlestick_chart),
        ("Violin Plot", violin_plot),
        ("Density Contour", density_contour),
        ("Line and Area Combined Chart", line_area_combined),
        ("3D Scatter Plot", scatter_3d),
        ("Stacked Bar Chart", bar_stacked),
        ("Treemap", treemap),
        ("Sunburst Chart", sunburst),

    ]

    # Iterate over chart functions and group them into rows of 3
    for i in range(0, len(chart_functions), 3):
        cols = st.columns(3)  # Create 3 columns for each row
        for col, (title, chart_function) in zip(cols, chart_functions[i : i + 3]):
            with col:  # Place each chart in its column
                render_chart_with_add_button(chart_function, title)

        # Add a container line for visual separation between rows
        st.markdown("---")


def configure_chart_workflow(chart_title, page_name):
    """Improved workflow for configuring a chart with real data."""
    st.write(f"## Configure Chart: {chart_title}")

    ### Step 1: Select and Save the Parquet File ###
    st.markdown("### Step 1: Select a `.parquet` File")
    data_dir = "./database"

    try:
        files = [f for f in os.listdir(data_dir) if f.endswith(".parquet")]
    except FileNotFoundError:
        st.error(f"The directory '{data_dir}' does not exist.")
        return

    if not files:
        st.warning("No `.parquet` files found in the 'database' directory.")
        return

    selected_file = st.selectbox("Select a `.parquet` file", files)
    file_path = os.path.join(data_dir, selected_file)

    if st.button("Save Selected File"):
        # Save the file selection to pages.json
        pages = pages_data.load_pages()
        page = next((p for p in pages if p["title"] == page_name), None)

        if page is None:
            page = {"title": page_name, "charts": []}
            pages.append(page)

        # Save the file path for this chart
        chart = next(
            (c for c in page["charts"] if c["chart_name"] == chart_title), None
        )
        if chart is None:
            chart = {
                "chart_name": chart_title,
                "file_path": file_path,
                "dimension": [],
                "measure": [],
                "date_column": [],
            }
            page["charts"].append(chart)
        else:
            chart["file_path"] = file_path

        pages_data.save_pages(pages)
        st.success(f"Selected file '{selected_file}' saved for '{chart_title}'.")

    ### Step 2: Slice the Parquet File ###
    st.markdown("### Step 2: Slice the Parquet File")
    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        st.error(f"Failed to read the selected file. Error: {e}")
        return

    st.subheader("Preview of the Selected DataFrame")
    st.write(df)

    available_dimensions = df.select_dtypes(
        exclude=["number", "datetime"]
    ).columns.tolist()
    available_measures = df.select_dtypes(include=["number"]).columns.tolist()
    available_date_columns = df.select_dtypes(include=["datetime"]).columns.tolist()

    dimensions = st.multiselect("Select Dimensions", available_dimensions)
    measures = st.multiselect("Select Measures", available_measures)
    date_columns = st.multiselect("Select Date Fields", available_date_columns)

    if st.button("Save Slice Configuration"):
        # Save dimensions, measures, and date fields to pages.json
        pages = pages_data.load_pages()
        page = next((p for p in pages if p["title"] == page_name), None)
        chart = next(
            (c for c in page["charts"] if c["chart_name"] == chart_title), None
        )

        if chart:
            chart["dimension"] = dimensions
            chart["measure"] = measures
            chart["date_column"] = date_columns
            pages_data.save_pages(pages)
            st.success(f"Slice configuration saved for '{chart_title}'.")

    ### Step 3: Set Default Options for the Dynamic Chart ###
    st.markdown("### Step 3: Set Default Options for the Chart")

    if dimensions and measures:
        default_dimension = dimensions[0]
        default_measure = measures[0]

        st.markdown(f"**Default Dimension Filter:** `{default_dimension}`")
        st.markdown(f"**Default Measure Filter:** `{default_measure}`")

        if st.button("Save Default Options"):
            pages = pages_data.load_pages()
            page = next((p for p in pages if p["title"] == page_name), None)
            chart = next(
                (c for c in page["charts"] if c["chart_name"] == chart_title), None
            )

            if chart:
                chart["default_dimension"] = default_dimension
                chart["default_measure"] = default_measure
                pages_data.save_pages(pages)
                st.success(f"Default options saved for '{chart_title}'.")


def render_nav_bar():
    """Renders the navigation bar and handles user interactions."""
    pages = pages_data.load_pages()

    hide_navigation = st.sidebar.toggle("Hide Navigation", False)

    # Sidebar navigation
    if not hide_navigation:
        st.sidebar.header("Navigation")
        mode = st.sidebar.segmented_control("Select Mode", ["Pages :material/bar_chart_4_bars:", "Setup Mode :material/manufacturing: "], default="Pages :material/bar_chart_4_bars:")
        if mode:
            mode = "Setup Mode" if "Setup" in mode else "View Pages"
            st.session_state.last_mode = mode
        else:
            st.info("Please select a mode.")
            st.stop()
        if mode == "Setup Mode":
            st.sidebar.subheader("Setup Options")
            setup_option = st.sidebar.radio(
                "What would you like to do? ",
                [
                    "Create Page",
                    "Delete Page",
                    "Rename Page",
                    "Portfolio",
                ],  # Added Portfolio here
                index=3,
            )

            if setup_option == "Create Page":
                create_page(pages)
            elif setup_option == "Delete Page":
                delete_page(pages)
            elif setup_option == "Rename Page":
                rename_page(pages)
            elif setup_option == "Portfolio":  # Display Portfolio Page
                portfolio_page()
            elif setup_option == "Edit Mode":
                view_pages(pages)
        else:
            view_pages(pages)
    else:
        view_pages(pages)


render_nav_bar()
