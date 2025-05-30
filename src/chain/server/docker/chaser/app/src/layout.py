from typing import Any

from dash import dcc, html


def get_layout() -> Any:
    return html.Div(
        [
            # Run選択・Plot管理用のメモリストア
            dcc.Store(id="selected-run", storage_type="memory"),
            dcc.Store(id="plots-store", storage_type="memory", data={}),
            html.Div(
                style={"display": "flex", "height": "100vh", "fontFamily": "Arial, sans-serif"},
                children=[
                    # 左ペイン: Experiment/Run/Metric 選択とAdd Plotボタン
                    html.Div(
                        style={
                            "width": "300px",
                            "borderRight": "1px solid #ddd",
                            "padding": "20px",
                            "backgroundColor": "#f9f9f9",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "15px",
                        },
                        children=[
                            html.H2("Experiments", style={"marginBottom": "10px", "color": "#333"}),
                            dcc.Dropdown(
                                id="experiment-dropdown",
                                options=[],
                                placeholder="Select an experiment",
                                clearable=False,
                                style={"marginBottom": "10px"},
                            ),
                            html.Div(id="run-list-container", style={"flex": "1", "overflowY": "auto"}),
                            dcc.Interval(id="reload-experiment-list", interval=3000, n_intervals=0),
                            html.H4("Metrics", style={"marginTop": "20px", "color": "#555"}),
                            html.Div(
                                id="metrics-list-container",
                                style={
                                    "height": "200px",
                                    "overflowY": "auto",
                                    "border": "1px solid #ccc",
                                    "padding": "8px",
                                    "borderRadius": "6px",
                                    "backgroundColor": "#fff",
                                    "fontSize": "14px",
                                    "color": "#222",
                                },
                            ),
                            html.Button(
                                "Add Plot",
                                id="add-plot-btn",
                                n_clicks=0,
                                disabled=True,
                                style={
                                    "marginTop": "10px",
                                    "padding": "10px 16px",
                                    "fontSize": "15px",
                                    "backgroundColor": "#cccccc",
                                    "color": "#666666",
                                    "border": "none",
                                    "borderRadius": "8px",
                                    "cursor": "not-allowed",
                                },
                            ),
                            html.Div(id="add-dummy", style={"display": "none"}),
                        ],
                    ),
                    html.Div(
                        id="main-content",
                        style={
                            "flex": "1",
                            "padding": "30px",
                            "backgroundColor": "#fff",
                            "color": "#444",
                            "overflowY": "auto",
                        },
                        children=[
                            html.H3("Select an experiment and a run from the left."),
                            html.Div(id="plots-container", style={"marginTop": "20px"}),
                        ],
                    ),
                ],
            ),
        ]
    )


def get_run_list(hierarchy, selected_run) -> Any:
    radio_options = []
    for parent_run in hierarchy[None]:
        parent_id = parent_run["id"]
        parent_name = parent_run["name"]
        is_selected_parent = selected_run == parent_id
        radio_options.append(
            {
                "label": html.Div(
                    parent_name,
                    style={
                        "padding": "10px 16px",
                        "fontSize": "15px",
                        "backgroundColor": "#007bff" if is_selected_parent else "white",
                        "color": "white" if is_selected_parent else "#007bff",
                        "border": "1px solid #007bff",
                        "borderRadius": "8px",
                        "textAlign": "left",
                        "marginBottom": "4px",
                        "cursor": "pointer",
                        "userSelect": "none",
                    },
                ),
                "value": parent_id,
            }
        )
        for child in hierarchy.get(parent_id, []):
            child_id = child["id"]
            is_selected_child = selected_run == child_id
            radio_options.append(
                {
                    "label": html.Div(
                        child["name"],
                        style={
                            "padding": "10px 16px",
                            "fontSize": "15px",
                            "backgroundColor": "#007bff" if is_selected_child else "white",
                            "color": "white" if is_selected_child else "#007bff",
                            "border": "1px solid #007bff",
                            "borderRadius": "6px",
                            "textAlign": "right",
                            "marginLeft": "auto",
                            "width": "80%",
                            "marginBottom": "2px",
                            "cursor": "pointer",
                            "userSelect": "none",
                        },
                    ),
                    "value": child_id,
                }
            )
    return html.Div(
        dcc.RadioItems(
            id="run-radio",
            options=radio_options,
            value=selected_run,
            labelStyle={"display": "block"},
            inputStyle={"display": "none"},
        )
    )


if __name__ == "__main__":
    pass
