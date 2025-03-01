import os
import re
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from streamlit import fragment, popover
import pandas as pd

def render_markdown():
    st.markdown(
        """
    <style>
    .stApp { margin: 0; padding: 0; }
    </style>
    """,
        unsafe_allow_html=True,
    )

def create_bar_chart_with_infinite_bars(data: dict, xaxis_title, yaxis_title, text_anotation, orientation) -> go.Figure:
    fig = go.Figure()
    for bar in data.get("bars", []):
        fig.add_trace(
            go.Bar(
                x=bar["x"],
                y=bar["y"],
                marker_color=bar.get("marker_color", None),
                text=bar.get("text", ""),
                textposition="auto",
                orientation=orientation,
            )
        )
    fig.update_layout(
        barmode="group",
        bargap=0.2,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        margin=dict(l=10, r=10, t=120, b=100)
    )
    fig.update_layout(clickmode='event+select')
    if text_anotation:
        fig.add_annotation(
            text=text_anotation,
            xref="paper",
            yref="paper",
            x=0.05,
            y=1.25,
            showarrow=False,
            font=dict(size=12, color="black"),
            align="left",
            xanchor="left",
            yanchor="top"
        )
    return fig

@fragment
def create_bar_chart_with_filters(chart: dict, df):
    filtered_df, selected_dimension, selected_measure, optional_info, _ = render_form(chart, df)
    chart_data = {
        "x": filtered_df[selected_dimension],
        "y": filtered_df[selected_measure],
    }
    if chart.get("invert"):
        chart_data = {
            "x": df[selected_measure],
            "y": df[selected_dimension],
        }
    fig = create_bar_chart_with_infinite_bars(
        data={"bars": [chart_data]},
        xaxis_title=selected_measure if chart.get("invert") else selected_dimension,
        yaxis_title=selected_dimension if chart.get("invert") else selected_measure,
        orientation="h" if chart.get("invert") else "v",
        text_anotation=optional_info
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart", on_select=lambda : None, config={'displayModeBar': True})
    return fig

def render_form(chart: dict, df: pd.DataFrame):
    optional_info = ""
    selected_dimension = False
    col_1, col_2 = st.columns(2)

    with col_1.popover("Filter"):
        if chart.get("date_column") and chart.get("type") != "Variance Comparison":
            df, optional_info_dict = create_filters(df, chart["file_path"], chart["chart_id"])
            for key, value in optional_info_dict.items():
                if "Selected Days" in key:
                    optional_info += f"{key}: {value} <br>"
                    continue
                if len(value) > 3:
                    optional_info += f"{key}: {', '.join(value[:3])}... <br>"
                else:
                    optional_info += f"{key}: {', '.join(value) if isinstance(value, list) else value} <br>"

        with st.container(  border=False):
            if not chart.get("dimension", None):
                chart["dimension"] = []
            for dimension, i in zip(chart["dimension"], range(len(chart["dimension"]))):
                selected_dimension = st.multiselect(
                    f"Select {dimension}",
                    ["All", *df.sort_values(by=chart["date_column"])[dimension].dropna().unique().tolist()],
                    key=f"{chart['chart_id']}_dimension{i}",
                    default=["All"],
                )
                if "All" not in selected_dimension and selected_dimension:
                    optional_info += f"<em>{dimension.upper()}</em>: {', '.join(selected_dimension)} <br>"
                    df = df[df[dimension].isin(selected_dimension)]
                elif not selected_dimension:
                    st.info("Please select at least one filter.")
            if chart.get("type") == "Bar Chart":
                selected_dimension = st.selectbox(
                    "Select Dimension",
                    chart["dimension"],
                    key=f"{chart['chart_id']}_dimension",
                )
            selected_measure = st.selectbox(
                "Select Measure",
                chart["measure"],
                key=f"{chart['chart_id']}_measure"
            )
            if chart["type"] == "Variance Comparison":
                df = df.sort_values(by="Year", ascending=False)
                prior_year = st.selectbox(
                    "Select Prior Year",
                    df["Year"].unique(),
                    key=f"{chart['chart_id']}_prior_year",
                    index=df["Year"].unique().tolist().index(df["Year"].max()) + 1,
                )
                this_year = st.selectbox(
                    "Select This Year",
                    df["Year"].unique(),
                    key=f"{chart['chart_id']}_this_year",
                    index=df["Year"].unique().tolist().index(df["Year"].max()),
                )
                if prior_year and this_year:
                    prior_year_quantity = df[df["Year"] == prior_year][selected_measure].sum()
                    this_year_quantity = df[df["Year"] == this_year][selected_measure].sum()
                    if prior_year > this_year:
                        st.form_submit_button("Apply Filter", use_container_width=True)
                        st.error("Prior Year must be less than This Year")
                        st.stop()
                    optional_info = {
                        "prior_year_quantity": prior_year_quantity,
                        "this_year_quantity": this_year_quantity,
                        "prior_year": prior_year,
                        "this_year": this_year,
                        "additional_infos": optional_info
                    }

            filtered_df = df
            if chart["type"] == "Bar Chart":
                filtered_df = df.groupby(chart.get("dimension")[0])[selected_measure].sum().reset_index()
            elif chart["type"] == "Slicer Chart":
                filtered_df = df.groupby(chart.get("dimension")).agg({selected_measure: "sum"}).reset_index()
            elif chart["type"] != "Variance Comparison" and chart.get("dimension", None):
                filtered_df = df.groupby(chart.get("dimension")[0])[selected_measure].sum().reset_index()
            filtered_df = filtered_df.sort_values(by=selected_measure, ascending=False)
    return filtered_df, selected_dimension, selected_measure, optional_info, col_2

def extract_row_number(position):
    return int(position[0].split(',')[0].replace('ROW', ''))

def create_rows(charts):
    charts.sort(key=lambda x: extract_row_number(x["position"]))
    new_rows = {
        "align_left": [],
        "align_right": [],
        "left_priority": [],
        "right_priority": [],
        "all_lines": [],
    }
    for chart in charts:
        if isinstance(chart["position"], list):
            for position in chart["position"]:
                numeros = re.findall(r"\d+", position)
                numeros = [int(num) for num in numeros]
                row_number = numeros[0]
                col_number = numeros[1]
                if col_number == 2 and len(chart["position"]) > 1:
                    continue
                if col_number == 2 and len(chart["position"]) == 1:
                    if row_number not in new_rows:
                        new_rows[row_number] = [chart["chart_id"]]
                    else:
                        new_rows[row_number].insert(1, chart["chart_id"])
                elif len(chart["position"]) == 3:
                    new_rows["all_lines"].append(row_number)
                    if row_number not in new_rows:
                        new_rows[row_number] = [chart["chart_id"]]
                    else:
                        new_rows[row_number].append(chart["chart_id"])
                    break
                elif col_number == 1 and len(chart["position"]) == 2:
                    if row_number not in new_rows:
                        new_rows[row_number] = [chart["chart_id"]]
                        new_rows["align_left"].append(row_number)
                        new_rows["left_priority"].append(row_number)
                    else:
                        new_rows[row_number].insert(0, chart["chart_id"])
                        new_rows["align_left"].append(row_number)
                        new_rows["left_priority"].append(row_number)
                elif col_number == 1 and len(chart["position"]) == 1:
                    if row_number not in new_rows:
                        new_rows[row_number] = [chart["chart_id"]]
                        new_rows["align_left"].append(row_number)
                    else:
                        new_rows[row_number].insert(0, chart["chart_id"])
                        new_rows["align_left"].append(row_number)
                elif col_number == 3 and len(chart["position"]) == 2:
                    if row_number not in new_rows:
                        new_rows[row_number] = [chart["chart_id"]]
                        new_rows["align_right"].append(row_number)
                        new_rows["right_priority"].append(row_number)
                    else:
                        new_rows[row_number].append(chart["chart_id"])
                        new_rows["align_right"].append(row_number)
                        new_rows["right_priority"].append(row_number)
                elif col_number == 3 and len(chart["position"]) == 1:
                    if row_number not in new_rows:
                        new_rows[row_number] = [chart["chart_id"]]
                        new_rows["align_right"].append(row_number)
                    else:
                        new_rows[row_number].append(chart["chart_id"])
                        new_rows["align_right"].append(row_number)
                break
        else:
            numbers = re.findall(r"\d+", chart["position"])
            numbers = [int(num) for num in numbers]
            row_number = numbers[0]
            col_number = numbers[1]
            if col_number == 2:
                if row_number not in new_rows:
                    new_rows[row_number] = [chart["chart_id"]]
                else:
                    new_rows[row_number].insert(1, chart["chart_id"])
            elif col_number == 1:
                if row_number not in new_rows:
                    new_rows[row_number] = [chart["chart_id"]]
                    new_rows["align_left"].append(row_number)
                else:
                    new_rows[row_number].insert(0, chart["chart_id"])
                    new_rows["align_left"].append(row_number)
            elif col_number == 3:
                if row_number not in new_rows:
                    new_rows[row_number] = [chart["chart_id"]]
                    new_rows["align_right"].append(row_number)
                else:
                    new_rows[row_number].append(chart["chart_id"])
                    new_rows["align_right"].append(row_number)
    for key, value in new_rows.items():
        if isinstance(key, str) and (("align" in key) or ("priority" in key) or ("all" in key)):
            continue
        elif len(value) == 1 and key in new_rows["all_lines"]:
            new_rows[key] = [(st.container(), value[0])]
        elif len(value) == 1 and key in new_rows["align_left"] and key in new_rows["left_priority"]:
            new_rows[key] = st.columns((2, 1), gap="large")
            new_rows[key] = [(new_rows[key][0], value[0]), (new_rows[key][1],)]
        elif len(value) == 2 and key not in new_rows["align_left"] and key not in new_rows["align_right"]:
            columns = st.columns((1, 1), gap="large")
            new_rows[key] = [(columns[0], value[0]), (columns[1], value[1])]
        elif len(value) == 2 and key in new_rows["align_left"] and key in new_rows["align_right"] and key not in new_rows["left_priority"] and key not in new_rows["right_priority"]:
            columns = st.columns((1, 1, 1), gap="large")
            new_rows[key] = [(columns[0], value[0]), (columns[1],), (columns[2], value[1])]
        elif len(value) == 2 and key in new_rows["align_left"] and key not in new_rows["right_priority"]:
            columns = st.columns((1, 1), gap="large")
            new_rows[key] = [(columns[0], value[0]), (columns[1], value[1])]
        elif len(value) == 2 and key in new_rows["align_right"] and key not in new_rows["left_priority"]:
            columns = st.columns((1, 2), gap="large")
            new_rows[key] = [(columns[0], value[0]), (columns[1], value[1])]
        elif len(value) == 1 and key in new_rows["align_right"] and key in new_rows["right_priority"]:
            new_rows[key] = st.columns((1, 2), gap="large")
            new_rows[key] = [(new_rows[key][0],), (new_rows[key][1], value[0])]
        elif len(value) == 1 and key in new_rows["align_left"] and key in new_rows["left_priority"]:
            new_rows[key] = st.columns((2, 1), gap="large")
            new_rows[key] = [(new_rows[key][0], value[0]), (new_rows[key][1],)]
        elif len(value) == 1 and key in new_rows["align_right"] and key not in new_rows["right_priority"]:
            new_rows[key] = st.columns((1, 2), gap="large")
            new_rows[key] = [(new_rows[key][0],), (new_rows[key][1], value[0])]
        elif len(value) == 1 and key in new_rows["align_left"] and key not in new_rows["left_priority"]:
            new_rows[key] = st.columns((1, 1, 1), gap="large")
            new_rows[key] = [(new_rows[key][0], value[0]), (new_rows[key][1],), (new_rows[key][2],)]
        elif len(value) == 1 and key not in new_rows["align_left"] and key not in new_rows["align_right"]:
            new_rows[key] = st.columns((1, 1, 1), gap="large")
            new_rows[key] = [(new_rows[key][0],), (new_rows[key][1], value[0]), (new_rows[key][2],)]
        elif len(value) == 3:
            columns = st.columns((1, 1, 1), gap="large")
            new_rows[key] = [(columns[0], value[0]), (columns[1], value[1]), (columns[2], value[2])]
    return new_rows

def create_year_and_month_week_and_day_columns(data, date_column):
    data[date_column] = pd.to_datetime(data[date_column], errors="coerce")
    data[date_column].dropna(inplace=True)
    data["Year"] = data[date_column].dt.year.astype("Int64")
    data["Month"] = data[date_column].dt.month
    data["Week"] = data[date_column].dt.isocalendar().week
    data["Day"] = data[date_column].dt.date
    data["Week_Display"] = data[date_column].dt.strftime("%A, %Y, %b")
    data["Month_Display"] = data[date_column].dt.strftime("%b")
    data["Month_Year"] = data[date_column].dt.strftime("%b, %Y")
    data["Week_Year"] = data[date_column].dt.strftime("%Y-W%U")

def create_filters(df, path, id_chart):
    optional_info = {}
    time_unit = st.segmented_control(
        "Select Time Unit",
        ["Year", "Month", "Week", "Day"],
        key=f"time_unit_{id_chart}",
        default="Year",
    )
    if time_unit == "Year" or time_unit == "Month" or time_unit == "Week":
        selected_time_unit = st.multiselect(
            "Select Year",
            ["All", *sorted(df["Year"].dropna().unique())],
            default="All",
            key=f"selected_year_{id_chart}",
        )
        if "All" not in selected_time_unit:
            df = df[df["Year"].isin(selected_time_unit)]
            optional_info["<em>Years</em>"] = [str(number) for number in selected_time_unit]
    if time_unit == "Month":
        selected_month = st.multiselect(
            "Select Month",
            ["All", *sorted(df["Month_Display"].dropna().unique(), key=lambda x: pd.to_datetime(x, format="%b").month)],
            default="All",
            key=f"selected_month_{id_chart}",
        )
        if "All" not in selected_month:
            optional_info["<em>Months</em>"] = selected_month
            df = df[df["Month_Display"].isin(selected_month)]
    elif time_unit == "Week":
        selected_week = st.multiselect(
            "Select Week",
            ["All", *sorted(df["Week_Year"].dropna().unique())],
            default="All",
            key=f"selected_week_{id_chart}",
        )
        if "All" not in selected_week:
            optional_info["<em>Weeks</em>"] = selected_week
            df = df[df["Week_Year"].isin(selected_week)]
    elif time_unit == "Day":
        selected_day = st.date_input(
            "Select Day",
            (df["Day"].dropna().min(), df["Day"].dropna().max()),
            df["Day"].dropna().min(),
            df["Day"].dropna().max(),
            key=f"selected_day_{id_chart}",
        )
        if len(selected_day) == 1:
            st.warning("Please select a valid date range.")
            st.stop()
        if len(selected_day) == 2:
            optional_info["<em>Selected Days</em>"] = f"{selected_day[0].strftime('%Y/%m/%d')} to {selected_day[1].strftime('%Y/%m/%d')}"
        df = df[(df["Day"] >= selected_day[0]) & (df["Day"] <= selected_day[1])]
    return df, optional_info

def render_chart_with_base_type_of_chart(chart):
    st.subheader(chart["chart_name"], divider=True, anchor=False)
    df = read_parquet(chart["file_path"], chart.get("date_column", False))
    if chart["type"] == "Bar Chart":
        fig = create_bar_chart_with_filters(chart, df)
    elif chart["type"] == "Line Chart":
        fig = create_line_chart_with_filters(chart, df)
    elif chart["type"] == "Pie Chart":
        fig = create_pie_chart_with_filters(chart, df)
    elif chart["type"] == "Scatter Plot":
        fig = create_scatter_chart_with_filters(chart, df)
    elif chart["type"] == "Slicer Chart":
        fig = create_slicer_chart(chart, df)
    elif chart["type"] == "Variance Comparison":
        fig = create_variance_comparison_bar_chart_with_filters(chart, df)
    elif chart["type"] == "Choropleth Map":
        fig = create_choropleth_map_with_filters(chart, df)

    if st.session_state["edit_mode_is_enabled"]:
        if st.button("Edit Chart :material/edit_square:", key=f"{chart['chart_id']}_edit", use_container_width=True):
            create_edit_form(chart, fig)
            pass

@st.dialog(title="Edit this chart", width="large")
def create_edit_form(chart, fig):
    if chart["type"] != "Slicer Chart":
        st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart_edit", on_select=lambda : None)
    df = read_parquet(chart["file_path"], chart.get("date_column", False))
    available_dimensions = df.select_dtypes(
        exclude=["number", "datetime"]
    ).columns.tolist()
    name_of_chart = st.text_input("Chart Name", chart.get("chart_name", ""))
    available_measures = df.select_dtypes(include=["number"]).columns.tolist()
    available_date_fields = df.select_dtypes(include=["datetime"]).columns.tolist()
    dimensions = st.multiselect("Select Dimension", available_dimensions, default=chart.get("dimension", []))
    measures = st.multiselect("Select Measure", available_measures, default=chart.get("measure", []))
    date_fields = st.multiselect("Select Date Field", available_date_fields, default=chart.get("date_column", []))
    from set_up_chart import get_available_positions
    from components.positions_component.src.streamlit_component_x import position_selector
    from set_up_chart import load_pages, save_pages
    import uuid
    available_positions = get_available_positions(st.session_state.name_of_actually_page)
    if not available_positions:
        st.warning(
            "No available positions on this page. Please remove an existing chart or select a different page."
        )
        return
    for position in chart.get("position", []):
        for available_position in available_positions:
            if position in available_position:
                available_positions.remove(available_position)
    st.markdown("Select New Position")
    selected_position = position_selector(positions=available_positions)
    
    if st.button("Save Changes", disabled=not bool(selected_position), use_container_width=True):
        chart_config = {
                "chart_name": name_of_chart,
                "type": chart.get("type"),
                "dimension": dimensions,
                "measure": measures,
                "date_column": date_fields,
                "dynamic_measures": measures,
                "file_path": chart.get("file_path"),
                "position": selected_position,
                }
        selected_page = st.session_state.name_of_actually_page
        pages = load_pages()
        for page in pages:
            if page["title"] == selected_page:
                for chart_old in page["charts"]:
                    if chart_old["chart_id"] == chart["chart_id"]:
                        page["charts"].remove(chart_old)
                        chart_config["chart_id"] = str(uuid.uuid4())
                        page["charts"].append(chart_config)
                        break
                break
        save_pages(pages)
        st.success("Chart edited successfully.")
        st.toast("Chart edited successfully.", icon=":material/check_circle:")
        from time import sleep
        sleep(2)
        st.rerun()

def create_choropleth_map(df: pd.DataFrame, measure: str, location_column: str, annotation: str = None) -> px.choropleth:
    if df[location_column].str.match(r"^[A-Z]{2}$").all():
        locationmode = "USA-states"
        scope = "usa"
    elif df[location_column].str.match(r"^[A-Z]{3}$").all():
        locationmode = "ISO-3"
        scope = "world"
    elif df[location_column].isin(["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
                                   "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
                                   "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
                                   "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
                                   "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
                                   "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
                                   "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
                                   "Wisconsin", "Wyoming"]).all():
        locationmode = "USA-states"
        scope = "usa"
    else:
        locationmode = "country names"
        scope = "world"
    data = df.groupby(location_column)[measure].sum().reset_index()
    fig_map = px.choropleth(
        data,
        locations=location_column,
        locationmode=locationmode,
        color=measure,
        color_continuous_scale="Viridis",
        scope=scope,
        labels={measure: measure},
    )
    fig_map.update_layout(
        yaxis=dict(tickformat=",.2f"),
        coloraxis_showscale=False,
        showlegend=False,
        margin=dict(l=10, r=10, t=120, b=0)
    )
    if annotation:
        fig_map.add_annotation(
            text=annotation,
            xref="paper",
            yref="paper",
            x=0.05,
            y=1.25,
            showarrow=False,
            font=dict(size=12, color="black"),
            align="left",
            xanchor="left",
            yanchor="top"
        )
    return fig_map

def create_choropleth_map_with_filters(chart: dict, df: pd.DataFrame):
    filtered_df, selected_dimension, selected_measure, optional_info, _ = render_form(chart, df)
    fig = create_choropleth_map(filtered_df, selected_measure, chart["dimension"][0], annotation=optional_info)
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart", on_select=lambda : None)
    return fig
def create_line_chart_with_infinite_lines(data: dict, xaxis_title, yaxis_title, annotation) -> go.Figure:
    fig = go.Figure()
    for line in data.get("lines", []):
        fig.add_trace(
            go.Scatter(
                x=line["x"],
                y=line["y"],
                mode="lines+markers",
                name=line.get("name", ""),
                marker_color=line.get("marker_color", None),
                text=line.get("text", ""),
                textposition="top center",
                orientation="h",
            )
        )
    fig.update_layout(
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        margin=dict(l=10, r=10, t=120, b=10)
    )
    if annotation:
        fig.add_annotation(
            text=annotation,
            xref="paper",
            yref="paper",
            x=0.05,
            y=1.25,
            showarrow=False,
            font=dict(size=12, color="black"),
            align="left",
            xanchor="left",
            yanchor="top"
        )
    return fig

@fragment
def create_line_chart_with_filters(chart: dict, df):
    filtered_df, selected_dimension, selected_measure, optional_info, _ = render_form(chart, df)
    fig = create_line_chart_with_infinite_lines(
        data={"lines": [{"x": filtered_df[chart.get("dimension")[0]], "y": filtered_df[selected_measure], "marker_color": "blue"}]},
        xaxis_title=chart.get("dimension")[0],
        yaxis_title=selected_measure,
        annotation=optional_info
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart", on_select=lambda : None)
    return fig
def create_pie_chart_with_infinite_slices(data: dict, annotation) -> go.Figure:
    fig = go.Figure()
    for slice in data.get("slices", []):
        fig.add_trace(
            go.Pie(
                labels=slice["labels"],
                values=slice["values"],
                hole=0.3,
                marker_colors=slice.get("marker_colors", None),
            )
        )
    fig.update_layout(
        margin=dict(l=10, r=10, t=120, b=10)
    )
    if annotation:
        fig.add_annotation(
            text=annotation,
            xref="paper",
            yref="paper",
            x=0.05,
            y=1.25,
            showarrow=False,
            font=dict(size=12, color="black"),
            align="left",
            xanchor="left",
            yanchor="top"
        )
    return fig

@fragment
def create_pie_chart_with_filters(chart: dict, df):
    filtered_df, selected_dimension, selected_measure, optional_info, _ = render_form(chart, df)
    fig = create_pie_chart_with_infinite_slices(
        data={"slices": [{"labels": filtered_df[chart.get("dimension")[0]], "values": filtered_df[selected_measure], "marker_colors": ["blue", "red", "green", "yellow"]}]},
        annotation=optional_info
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart", on_select=lambda : None)
    return fig
def create_scatter_chart_with_infinite_scatters(data: dict, xaxis_title, yaxis_title, annotation) -> go.Figure:
    fig = go.Figure()
    for scatter in data.get("scatters", []):
        fig.add_trace(
            go.Scatter(
                x=scatter["x"],
                y=scatter["y"],
                mode="markers",
                marker_color=scatter["marker_color"],
                text=scatter.get("text", ""),
                textposition="top center",
            )
        )
    fig.update_layout(
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        margin=dict(l=10, r=10, t=120, b=10)
    )
    if annotation:
        fig.add_annotation(
            text=annotation,
            xref="paper",
            yref="paper",
            x=0.05,
            y=1.25,
            showarrow=False,
            font=dict(size=12, color="black"),
            align="left",
            xanchor="left",
            yanchor="top"
        )
    return fig

@fragment
def create_scatter_chart_with_filters(chart: dict, df):
    filtered_df, selected_dimension, selected_measure, optional_info, _ = render_form(chart, df)
    fig = create_scatter_chart_with_infinite_scatters(
        data={"scatters": [{"x": filtered_df[chart.get("dimension")[0]], "y": filtered_df[selected_measure], "marker_color": "blue"}]},
        xaxis_title=chart.get("dimension")[0],
        yaxis_title=selected_measure,
        annotation=optional_info
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart", on_select=lambda : None)
    return fig
@fragment
def create_slicer_chart(chart, df):
    filtered_df, _, _, optional_info,col_2  = render_form(chart, df)
    with col_2:
        if optional_info:
            with st.container(height=80, border=False):
                st.markdown(optional_info, unsafe_allow_html=True)

    st.dataframe(filtered_df, hide_index=True, use_container_width=True, height=500)

@fragment
def create_variance_comparison_bar_chart_with_filters(chart, df):
    _, _, measure, optional_info, _ = render_form(chart, df)
    fig = create_variance_comparison_bar_chart(
        total_this_year=float(optional_info["this_year_quantity"]),
        total_prior_year=float(optional_info["prior_year_quantity"]),
        xaxis_title=measure,
        prior_year=optional_info["prior_year"],
        this_year=optional_info["this_year"],
        additional_info=optional_info["additional_infos"]
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart", on_select=lambda : None)
    return fig
def create_variance_comparison_bar_chart(total_this_year: float, total_prior_year: float, xaxis_title: str, prior_year: int, this_year: int, additional_info: str) -> go.Figure:
    variance = total_this_year - total_prior_year
    variance_percentage = (variance / total_prior_year) * 100 if total_prior_year != 0 else float("inf")
    total_this_year_fmt = f"{total_this_year:,.2f}"
    total_prior_year_fmt = f"{total_prior_year:,.2f}"
    variance_fmt = f"{variance:,.2f}"
    variance_percentage_fmt = f"{variance_percentage:,.2f}%"
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[variance],
            y=["Variance"],
            name="Variance",
            marker_color="darkgray" if variance >= 0 else "red",
            text=f"{variance_fmt}\n({variance_percentage_fmt})",
            textposition="outside" if variance >= 0 else "none",
            orientation="h",
            width=0.8,
        )
    )
    fig.add_trace(
        go.Bar(
            x=[total_prior_year],
            y=["Prior Year"],
            name="Prior Year",
            marker_color="darkgreen",
            text=total_prior_year_fmt,
            textposition="auto",
            orientation="h",
            width=0.8,
        )
    )
    fig.add_trace(
        go.Bar(
            x=[total_this_year],
            y=["This Year"],
            name="This Year",
            marker_color="darkblue",
            text=total_this_year_fmt,
            textposition="auto",
            orientation="h",
            width=0.8,
        )
    )
    fig.update_layout(
        barmode="group",
        bargap=0.05,
        showlegend=True,
        legend=dict(x=1.02, y=1, bgcolor="rgba(255,255,255,0.5)", bordercolor="black", borderwidth=1),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        xaxis=dict(title=xaxis_title, showticklabels=True, showgrid=False, zeroline=False),
        margin=dict(l=10, r=10, t=120, b=60)
    )
    fig.add_annotation(
        text=f"Prior Year: {prior_year} | This Year: {this_year} <br> {additional_info if additional_info else ''}",
        xref="paper",
        yref="paper",
        x=0.05,
        y=1.25,
        showarrow=False,
        font=dict(size=12, color="black"),
        align="left",
        xanchor="left",
        yanchor="top"
    )
    return fig

@st.cache_data
def read_parquet(path: str, column_data: bool | str = False):
    df = pd.read_parquet(path)
    if column_data:
        create_year_and_month_week_and_day_columns(df, column_data[0])
    return df