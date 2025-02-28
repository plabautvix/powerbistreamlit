import os
import re
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from streamlit import fragment, popover
import pandas as pd


def render_markdown():
    """
    Renders the markdown header for the setup.
    """
    st.markdown(
        """
    <style>
    .stApp { margin: 0; padding: 0; }
    </style>
    """,
        unsafe_allow_html=True,
    )


def create_bar_chart_with_infinite_bars(data: dict, title_of_chart: str, xaxis_title, yaxis_title, text_anotation, orientation) -> go.Figure:
    """
    Create a bar chart with the given data.
    """
    fig = go.Figure()

    for bar in data.get("bars", []):
        fig.add_trace(
            go.Bar(
                x=bar["x"],
                y=bar["y"],
                marker_color=bar.get("marker_color", None),
                text=bar.get("text", ""),
                textposition="auto",
                orientation=orientation
            )
        )

    fig.update_layout(title=title_of_chart, barmode="group", bargap=0.2, xaxis_title=xaxis_title, yaxis_title=yaxis_title)
    fig.add_annotation(
    text= text_anotation,
    xref="paper", yref="paper",
    x=0.5, y=1.3,  # Posição acima do gráfico
    showarrow=False,
    font=dict(size=12, color="black")
    )

    return fig


@fragment
def create_bar_chart_with_filters(chart: dict, df ):
    """
    This function is used for creating a bar chart with filters.

    Args:
    chart: dict
    df: DataFrame

    Returns:
    None
    """
    filtered_df, selected_dimension, selected_measure, optional_info = render_form(chart, df)
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
        data={
            "bars": [
                chart_data
            ]
        },
        title_of_chart=chart["chart_name"],
        xaxis_title=selected_measure if chart.get("invert") else selected_dimension,
        yaxis_title=selected_dimension if chart.get("invert") else selected_measure,
        orientation="h" if chart.get("invert") else "v",
        text_anotation=optional_info
    )

    # Plot the chart
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart")



def render_form(
    chart: dict,
    df: pd.DataFrame,
    
):
    """
    This function is used for rendering the form for the filters.
    """
    optional_info = False
    optional_info = ""
    selected_dimension = False

    with st.popover("Filter"):
        if chart.get("date_column") and chart.get("type") != "Variance Comparison":
            df, optional_info_dict = create_filters(df,chart["file_path"], chart["chart_id"])
            for key, value in optional_info_dict.items():
                if len(value) > 3:
                    optional_info += f"{key}: {', '.join(value[:3])}... <br>"
                else:  
                    optional_info += f"{key}: {', '.join(value) if isinstance(value, list) else value} <br>"

        with st.form(key=f"{chart['chart_id']}_form", border=False):
            for dimension, i in zip(chart["dimension"], range(len(chart["dimension"]))):
                selected_dimension = st.multiselect(
                    f"Select {dimension}",
                    [
                        "All",
                        *df.sort_values(by=chart["date_column"])[dimension]
                        .unique()
                        .tolist(),
                    ],
                    key=f"{chart['chart_id']}_dimension{i}",
                    default=["All"],
                )
                if "All" not in selected_dimension and selected_dimension:
                    optional_info += f"Filters for {dimension.upper()}: {', '.join(selected_dimension)} <br>"
                    df = df[df[dimension].isin(selected_dimension)]
                elif not selected_dimension:
                    st.info("Please select at least one filter.")


            if chart["type"] == "Slicer Chart":
                selected_dimension = st.multiselect(
                    "Select Dimensions",
                    chart["dimension"],
                    key=f"{chart['chart_id']}_dimension",
                    default=chart["dimension"],
                )
            else:
                selected_dimension = st.selectbox(
                    "Select Dimension",
                    chart["dimension"],
                    key=f"{chart['chart_id']}_dimension",
                )
            if not selected_dimension:
                st.info("Please select at least one filter.")
            selected_measure = st.selectbox(
                "Select Measure", chart["measure"], key=f"{chart['chart_id']}_measure"
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
                        "this_year": this_year
                    }
            if st.form_submit_button("Apply Filter", use_container_width=True):
                st.session_state["selected_dimension"] = selected_dimension
                st.session_state["selected_measure"] = selected_measure
                st.rerun()
            # Update filtered DataFrame based on selections
            filtered_df = df
            if chart["type"] == "Slicer Chart":
                filtered_df = df.groupby(selected_dimension).agg({selected_measure: "sum"}).reset_index()
            elif chart["type"] != "Variance Comparison":
                filtered_df = (
                    df.groupby([selected_dimension])[selected_measure].sum().reset_index()
                )
            filtered_df = filtered_df.sort_values(by=selected_measure, ascending=False)
        
    return filtered_df, selected_dimension, selected_measure, optional_info


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
        if (
            isinstance(key, str)
            and (("align" in key)
            or ("priority" in key)
            or ("all" in key))
        ):
            continue
        elif len(value) == 1 and key in new_rows["all_lines"]:
            new_rows[key] = [(st.container(), value[0])]
        elif (
            len(value) == 1
            and key in new_rows["align_left"]
            and key in new_rows["left_priority"]
        ):
            new_rows[key] = st.columns((2, 1))
            new_rows[key] = [(new_rows[key][0], value[0]), (new_rows[key][1],)]
        elif (
            len(value) == 2
            and key not in new_rows["align_left"]
            and key not in new_rows["align_right"]
        ):
            columns = st.columns((1, 1))
            new_rows[key] = [(columns[0], value[0]), (columns[1], value[1])]
        elif (
            len(value) == 2
            and key in new_rows["align_left"]
            and key in new_rows["align_right"]
            and key not in new_rows["left_priority"]
            and key not in new_rows["right_priority"]
        ):
            columns = st.columns((1, 1, 1))

            new_rows[key] = [
                (columns[0], value[0]),
                (columns[1],),
                (columns[2], value[1]),
            ]
        elif (
            len(value) == 2
            and key in new_rows["align_left"]
            and key not in new_rows["right_priority"]
        ):
            columns = st.columns((1, 1))
            new_rows[key] = [(columns[0], value[0]), (columns[1], value[1])]

        elif (
            len(value) == 2
            and key in new_rows["align_right"]
            and key not in new_rows["left_priority"]
        ):
            columns = st.columns((1, 2))
            new_rows[key] = [(columns[0], value[0]), (columns[1], value[1])]

        elif (
            len(value) == 1
            and key in new_rows["align_right"]
            and key in new_rows["right_priority"]
        ):
            new_rows[key] = st.columns((1, 2))
            new_rows[key] = [(new_rows[key][0],), (new_rows[key][1], value[0])]

        elif (
            len(value) == 1
            and key in new_rows["align_left"]
            and key in new_rows["left_priority"]
        ):
            new_rows[key] = st.columns((2, 1))
            new_rows[key] = [(new_rows[key][0], value[0]), (new_rows[key][1],)]

        elif (
            len(value) == 1
            and key in new_rows["align_right"]
            and key not in new_rows["right_priority"]
        ):
            new_rows[key] = st.columns((1, 2))
            new_rows[key] = [(new_rows[key][0],), (new_rows[key][1], value[0])]

        elif (
            len(value) == 1
            and key in new_rows["align_left"]
            and key not in new_rows["left_priority"]
        ):
            new_rows[key] = st.columns((1, 1, 1))
            new_rows[key] = [
                (new_rows[key][0], value[0]),
                (new_rows[key][1],),
                (new_rows[key][2],),
            ]

        elif (
            len(value) == 1
            and key not in new_rows["align_left"]
            and key not in new_rows["align_right"]
        ):
            new_rows[key] = st.columns((1, 1, 1))
            new_rows[key] = [
                (new_rows[key][0],),
                (new_rows[key][1], value[0]),
                (new_rows[key][2],),
            ]
        elif len(value) == 3:
            columns = st.columns((1, 1, 1))
            new_rows[key] = [
                (columns[0], value[0]),
                (columns[1], value[1]),
                (columns[2], value[2]),
            ]

    return new_rows
import pandas as pd
import streamlit as st

def create_year_and_month_week_and_day_columns(data, date_column):
    """
    Create Year, Month, Week, and Day columns from a date column in a DataFrame.

    This function get the data and a date column and create Year, Month, Week, and Day columns.

    The columns created are:
    - Year: Extract the year from the date column.
    - Month: Extract the month from the date column.
    - Week: Extract the week from the date column.
    - Day: Extract the day from the date column.
    - Week_Display: Format the date column to show the day of the week, year, and month.
    - Month_Display: Format the date column to show the month.
    - Month_Year: Format the date column to show the month and year.
    - Week_Year: Combine year and week for better clarity.
    Args:
    data: DataFrame
    date_column: str

    Returns:
    None
    """

    data[date_column] = pd.to_datetime(data[date_column], errors="coerce")
    data[date_column].dropna(inplace=True)
    data["Year"] = data[date_column].dt.year.astype("Int64")
    data["Month"] = data[date_column].dt.month
    data["Week"] = data[date_column].dt.isocalendar().week
    data["Day"] = data[date_column].dt.date
    data["Week_Display"] = data[date_column].dt.strftime("%A, %Y, %b")
    data["Month_Display"] = data[date_column].dt.strftime("%b")
    data["Month_Year"] = data[date_column].dt.strftime("%b, %Y")
    data["Week_Year"] = data[date_column].dt.strftime("%Y-W%U")  # Combina ano e semana


def create_filters(df, path, id_chart):
    """
    Create a sidebar with filters for the date column in the DataFrame.

    Args:
    df: DataFrame
    date_column: str

    Returns:
    DataFrame
    """
    optional_info = {}
    time_unit = st.segmented_control(
        "Select Time Unit",
        ["Year", "Month", "Week", "Day"],
        key=f"time_unit_{id_chart}",
        default="Year",
    )
    default_year = st.session_state.get(f"selected_year_{id_chart}","All")
    if time_unit == "Year":
        selected_time_unit = st.multiselect(
            "Select Year",
            ["All",*sorted(df["Year"].dropna().unique())],
            default=default_year,
            key=f"selected_year_{id_chart}",
        )
        if "All" not in selected_time_unit:
            df = df[df["Year"].isin(selected_time_unit)]
            optional_info["Selected Years"] = [str(number) for number in selected_time_unit]

    elif time_unit == "Month":
        selected_year = st.multiselect(
            "Select Year",
            ["All",*sorted(df["Year"].dropna().unique())],
            default=default_year,
            key=f"selected_year_{id_chart}",
        )
        if "All" not in selected_year:
            df = df[df["Year"].isin(selected_year)]
            optional_info["Selected Years"] = [str(number) for number in selected_year]

        selected_month = st.multiselect(
            "Select Month",
            ["All", *sorted(df["Month_Display"].dropna().unique(), key=lambda x: pd.to_datetime(x, format="%b").month)],
            default="All",
            key=f"selected_month_{id_chart}",
        )
        if "All" not in selected_month:
            optional_info["Selected Months"] = selected_month
            df = df[df["Month_Display"].isin(selected_month)]

    elif time_unit == "Week":
        selected_year = st.multiselect(
            "Select Year",
            ["All",*sorted(df["Year"].dropna().unique())],  # Ordena os anos
            default=default_year,
            key=f"selected_year_{id_chart}",
        )
        if "All" not in selected_year:
            df = df[df["Year"].isin(selected_year)]
            optional_info["Selected Years"] = [str(number) for number in selected_year]
    
        selected_week = st.multiselect(
            "Select Week",
            ["All", *sorted(df["Week_Year"].dropna().unique())],  # Ordena as semanas
            default="All",
            key=f"selected_week_{id_chart}",
        )
        if "All" not in selected_week:
            optional_info["Selected Weeks"] = selected_week
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
        
        optional_info["Selected Days"] = selected_day
        df = df[
            (df["Day"] >= selected_day[0]) & (df["Day"] <= selected_day[1])
        ]

    return df, optional_info

def render_chart_with_base_type_of_chart(chart):
    """
    Render a chart based on the base type of chart.

    Args:
    chart: dict
    df: DataFrame

    Returns:
    None
    """
    df = read_parquet(chart["file_path"], chart.get("date_column", False))
    if chart["type"] == "Bar Chart":
        create_bar_chart_with_filters(chart, df)
    elif chart["type"] == "Line Chart":
        create_line_chart_with_filters(chart, df)
    elif chart["type"] == "Pie Chart":
        create_pie_chart_with_filters(chart, df)
    elif chart["type"] == "Scatter Plot":
        create_scatter_chart_with_filters(chart, df)
    elif chart["type"] == "Slicer Chart":
        create_slicer_chart(chart, df)
    elif chart["type"] == "Variance Comparison":
        create_variance_comparison_bar_chart_with_filters(
            chart, df
        )
    elif chart["type"] == "Choropleth Map":
        create_choropleth_map_with_filters(chart, df)


def create_choropleth_map(
    df: pd.DataFrame, measure: str, location_column: str, title: str, annotation: str = None
) -> px.choropleth:
    """
    Create a choropleth map representing a measure (e.g., sales, population) by country or state.
    The function automatically detects whether the location column contains country names, ISO-3 codes,
    US state names, or US state codes.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the data.
    measure : str
        The measure to be displayed on the map (e.g., sales, revenue, population).
    location_column : str
        The name of the column containing the location data (country names, ISO-3 codes, US state names, or US state codes).
    title : str
        The title of the choropleth map.
    annotation : str
        An annotation to be displayed above the chart.

    Returns
    -------
    px.choropleth
        A Plotly choropleth map representing the measure by location.
    """
    # Verifica o tipo de dado na coluna de localização
    if df[location_column].str.match(r"^[A-Z]{2}$").all():  # Códigos de estados dos EUA (2 letras maiúsculas)
        locationmode = "USA-states"
        scope = "usa"
    elif df[location_column].str.match(r"^[A-Z]{3}$").all():  # Códigos ISO-3 (3 letras maiúsculas)
        locationmode = "ISO-3"
        scope = "world"
    elif df[location_column].isin(["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
                                   "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
                                   "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
                                   "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
                                   "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
                                   "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
                                   "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
                                   "Wisconsin", "Wyoming"]).all():  # Nomes de estados dos EUA
        locationmode = "USA-states"
        scope = "usa"
    else:  # Assume que são nomes de países
        locationmode = "country names"
        scope = "world"

    # Group data by location and calculate the sum of the measure (if needed)
    data = df.groupby(location_column)[measure].sum().reset_index()

    # Create the choropleth map
    fig_map = px.choropleth(
        data,
        locations=location_column,  # Coluna com localizações
        locationmode=locationmode,  # Modo de localização dinâmico
        color=measure,  # Medida a ser representada
        color_continuous_scale="Viridis",  # Escala de cores
        scope=scope,  # Escopo dinâmico
        labels={measure: measure},  # Rótulos para a legenda
        title=title,  # Título do mapa
    )

    # Ajustes de layout
    fig_map.update_layout(
        yaxis=dict(tickformat=",.2f"),
        showlegend=False,  # Ocultar a legenda
    )

    # Adicionar anotação (se fornecida)
    if annotation:
        fig_map.add_annotation(
            text=annotation,
            xref="paper", yref="paper",
            x=0.5, y=1.3,  # Posição acima do gráfico
            showarrow=False,
            font=dict(size=12, color="black")
        )

    return fig_map

def create_choropleth_map_with_filters(chart: dict, df: pd.DataFrame):
    """
    Create a choropleth map with filters.

    Args:
    chart: dict
    df: DataFrame

    Returns:
    None
    """
    filtered_df, selected_dimension, selected_measure, optional_info = render_form(chart, df)
    fig = create_choropleth_map(filtered_df, selected_measure, selected_dimension, title=chart["chart_name"], annotation=optional_info)

    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart")


def create_line_chart_with_infinite_lines(data: dict, title_of_chart, xaxis_title, yaxis_title, annotation) -> go.Figure:
    """
    Create a line chart with the given data.
    """
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

    fig.update_layout(title=title_of_chart, xaxis_title=xaxis_title, yaxis_title=yaxis_title)
    fig.add_annotation(
        text=annotation,
        xref="paper", yref="paper",
        x=0.5, y=1.3,  # Posição acima do gráfico
        showarrow=False,
        font=dict(size=12, color="black")
    )

    return fig

@fragment
def create_line_chart_with_filters(chart: dict, df):
    """
    This function is used for creating a line chart with filters.

    Args:
    chart: dict
    df: DataFrame

    Returns:
    None
    """
    filtered_df, selected_dimension, selected_measure, optional_info= render_form(chart, df)
    fig = create_line_chart_with_infinite_lines(
        data={
            "lines": [
                {
                    "x": filtered_df[selected_dimension],
                    "y": filtered_df[selected_measure],
                    "marker_color": "blue",
                }
            ]
        },
        title_of_chart=chart["chart_name"],
        xaxis_title=selected_dimension,
        yaxis_title=selected_measure,
        annotation=optional_info
    )

    # Plot the chart
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart")
    
    
def create_pie_chart_with_infinite_slices(data: dict, title_of_chart: str, annotation) -> go.Figure:
    """
    Create a pie chart with the given data.
    """
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

    fig.update_layout(title=title_of_chart)
    fig.add_annotation(
    text=annotation,
    xref="paper", yref="paper",
    x=0.5, y=1.3,  # Posição acima do gráfico
    showarrow=False,
    font=dict(size=12, color="black")
    )
    return fig

@fragment
def create_pie_chart_with_filters(chart: dict, df):
    """
    This function is used for creating a pie chart with filters.

    Args:
    chart: dict
    df: DataFrame

    Returns:
    None
    """
    filtered_df, selected_dimension, selected_measure ,optional_info= render_form(chart, df)
    fig = create_pie_chart_with_infinite_slices(
        data={
            "slices": [
                {
                    "labels": filtered_df[selected_dimension],
                    "values": filtered_df[selected_measure],
                    "marker_colors": ["blue", "red", "green", "yellow"],
                }
            ]
        },
        title_of_chart=chart["chart_name"],
        annotation=optional_info
    )

    # Plot the chart
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart")
    
def create_scatter_chart_with_infinite_scatters(
    data: dict, title_of_chart: str, xaxis_title, yaxis_title, annotation
) -> go.Figure:
    """
    Create a scatter chart with the given data.
    """
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

    fig.update_layout(title=title_of_chart, xaxis_title=xaxis_title, yaxis_title=yaxis_title)
    fig.add_annotation(
        text=annotation,
        xref="paper", yref="paper",
        x=0.5, y=1.3,  # Posição acima do gráfico
        showarrow=False,
        font=dict(size=12, color="black")
        )
    return fig

@fragment
def create_scatter_chart_with_filters(chart: dict, df):
    """
    This function is used for creating a scatter chart with filters.

    Args:
    chart: dict
    df: DataFrame

    Returns:
    None
    """
    filtered_df, selected_dimension, selected_measure, optional_info = render_form(chart, df)
    fig = create_scatter_chart_with_infinite_scatters(
        data={
            "scatters": [
                {
                    "x": filtered_df[selected_dimension],
                    "y": filtered_df[selected_measure],
                    "marker_color": "blue",
                }
            ]
        },
        title_of_chart=chart["chart_name"],
        xaxis_title=selected_dimension,
        yaxis_title=selected_measure,
        annotation=optional_info
    )

    # Plot the chart
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart")
    
@fragment
def create_slicer_chart(chart, df):
    """
    This function is used for creating a slicer chart.

    Args:
    chart: dict
    df: DataFrame

    Returns:
    None
    """
    filtered_df =  render_form(chart, df)[0]
    st.dataframe(filtered_df, hide_index=True, use_container_width=True, height=500)

@fragment
def create_variance_comparison_bar_chart_with_filters(chart, df):
    """
    This function is used for creating a variance comparison bar chart with filters.

    Args:
    chart: dict
    df: DataFrame

    Returns:
    None
    """
    _, _, measure, optional_info = render_form(chart, df)
    fig = create_variance_comparison_bar_chart(
        total_this_year=float(optional_info["this_year_quantity"]),
        total_prior_year=float(optional_info["prior_year_quantity"]),
        xaxis_title=measure,
        title=chart["chart_name"],
        prior_year=optional_info["prior_year"],
        this_year=optional_info["this_year"]
    )

    # Plot the chart
    st.plotly_chart(fig, use_container_width=True, key=f"{chart['chart_id']}_chart")

import plotly.graph_objects as go

def create_variance_comparison_bar_chart(
    total_this_year: float, total_prior_year: float, xaxis_title: str, title: str, prior_year: int, this_year: int
) -> go.Figure:
    """
    Create a bar chart to compare the variance between the current year and the prior year, including variance percentage.

    Parameters

    total_this_year : float
        The total value for the current year.
    total_prior_year : float
        The total value for the prior year.
    xaxis_title : str
        The title for the x-axis.
    title : str
        The title for the chart.    
    Returns

    go.Figure
        A Plotly figure object containing the bar chart.
    """
    # Calculate variance and percentage
    variance = total_this_year - total_prior_year
    variance_percentage = (
        (variance / total_prior_year) * 100
        if total_prior_year != 0
        else float("inf")
    )

    # Format numbers for better readability
    total_this_year_fmt = f"{total_this_year:,.2f}"
    total_prior_year_fmt = f"{total_prior_year:,.2f}"
    variance_fmt = f"{variance:,.2f}"
    variance_percentage_fmt = f"{variance_percentage:,.2f}%"

    # Create the figure
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=[variance],
            y=["Variance"],
            name="Variance",  # Nome para a legenda
            marker_color="darkgray" if variance >= 0 else "red",
            text=f"{variance_fmt}\n({variance_percentage_fmt})",
            textposition="outside" if variance >= 0 else "none",
            orientation="h",  # Horizontal orientation
            width=0.8,  # Increase bar width
        )
    )

    fig.add_trace(
        go.Bar(
            x=[total_prior_year],
            y=["Prior Year"],
            name="Prior Year",  # Nome para a legenda
            marker_color="darkgreen",
            text=total_prior_year_fmt,
            textposition="auto",
            orientation="h",  # Horizontal orientation
            width=0.8,  # Increase bar width
        )
    )

    fig.add_trace(
        go.Bar(
            x=[total_this_year],
            y=["This Year"],
            name="This Year",  # Nome para a legenda
            marker_color="darkblue",
            text=total_this_year_fmt,
            textposition="auto",
            orientation="h",  # Horizontal orientation
            width=0.8,  # Increase bar width
        )
    )

    # Update layout to reduce gap between bars and customize appearance
    fig.update_layout(
        title=title,
        barmode="group",
        bargap=0.05,  # Reduce the gap between bars
        showlegend=True,  # Exibir a legenda
        legend=dict(
            x=1.02,  # Posição da legenda (fora do gráfico)
            y=1,
            bgcolor="rgba(255,255,255,0.5)",  # Fundo semi-transparente para melhor leitura
            bordercolor="black",
            borderwidth=1
        ),
        yaxis=dict(
            showticklabels=False,  # Hide y-axis tick labels
            showgrid=False,  # Hide grid lines
            zeroline=False,  # Hide the zero line
        ),
        xaxis=dict(
            title=xaxis_title,  # Adiciona título ao eixo X
            showticklabels=True,  # Show x-axis tick labels
            showgrid=False,  # Hide grid lines
            zeroline=False,  # Hide the zero line
        ),
    )
    fig.add_annotation(
        text=f"Prior Year: {prior_year} | This Year: {this_year}",
        xref="paper", yref="paper",
        x=0.5, y=1.3,  # Posição acima do gráfico
        showarrow=False,
        font=dict(size=12, color="black")
        )
    return fig

@st.cache_data
def read_parquet(path: str, column_data: bool | str = False):
    """
    Read a parquet file from a given path.

    Args:
        path: str
            The path to the parquet file.
    Returns:
        DataFrame
    """
    df = pd.read_parquet(path)
    if column_data:
        create_year_and_month_week_and_day_columns(df, column_data[0])
    return df
