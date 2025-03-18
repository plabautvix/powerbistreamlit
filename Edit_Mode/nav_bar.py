import time
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import os
import pages_data
from examples import Examples
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
        edit_mode_is_enabled = st.sidebar.toggle("Edit Mode :material/edit:", False)
        st.session_state["edit_mode_is_enabled"] = edit_mode_is_enabled

        selected_page = st.sidebar.selectbox(
            "Select Page", [page["title"] for page in pages], index=0
        )
        
        
        if edit_mode_is_enabled:
            st.toast("Edit Mode is Enabled :material/check_circle:")
            col1, col2 = st.columns([1, 4])
            render_button_for_add_chart()
            with col2:
                with st.popover(":red[Delete Chart]", use_container_width=True):
                    container = st.container()
        st.session_state["last_page_selected"] = selected_page
        page = next((p for p in pages if p["title"] == selected_page), None)
        if not container is False:
            with container:
                delete_chart(pages, selected_page, page)
        if page:
            if page.get("with_title"):
                st.title(page["title"], anchor=False)
            st.session_state["name_of_actually_page"] = page["title"]
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


def render_button_for_add_chart():
    
    with st.sidebar.popover("", use_container_width=True, icon=":material/add_chart:"):
        portfolio_page()



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

            chart_function()  # Render the chart

            # Add button below each chart
            if st.button(f"Add '{title}'", key=f"add_{title}"):
                st.session_state.configure_chart = True
                st.session_state.chart_to_configure = title
                cadastre_form()
                # st.rerun()

    
    examples = Examples(category_df, df)
    # Group charts into rows of 3
    chart_functions = [
        ("Bar Chart", examples.bar_chart),
        ("Variance Comparison", examples.create_variance_comparison_bar_chart),
        ("Slicer Chart", examples.slicer_chart),
        ("Choropleth Map", examples.choropleth_map),
        ("Line Chart", examples.line_chart),
        ("Pie Chart", examples.pie_chart),
        ("Scatter Plot", examples.scatter_plot),
        ("Histogram", examples.histogram),
        ("Box Plot", examples.box_plot),
        ("Heatmap", examples.heatmap),
        ("Area Chart", examples.area_chart),
        ("Radar Chart", examples.radar_chart),
        ("Bubble Chart", examples.bubble_chart),
        ("Donut Chart", examples.donut_chart),
        ("Candlestick Chart", examples.candlestick_chart),
        ("Violin Plot", examples.violin_plot),
        ("Density Contour", examples.density_contour),
        ("Line and Area Combined Chart", examples.line_area_combined),
        ("3D Scatter Plot", examples.scatter_3d),
        ("Stacked Bar Chart", examples.bar_stacked),
        ("Treemap", examples.treemap),
        ("Sunburst Chart", examples.sunburst),

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
