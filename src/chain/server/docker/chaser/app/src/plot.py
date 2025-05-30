from dash import dcc, html


def plot_card(plot_id, figure, all_metrics, metric, n_dim: int = 1, dim: int = 1):
    return html.Div(
        [
            html.Div(
                [
                    dcc.Dropdown(
                        id={"type": "metric-dropdown", "index": plot_id},
                        options=[{"label": m, "value": m} for m in all_metrics],
                        value=metric,
                        clearable=False,
                        style={
                            "width": "200px",
                            "height": "40px",
                            "fontSize": "16px",
                            "borderRadius": "8px",
                        },
                    ),
                    dcc.Input(
                        id={"type": "dim-input", "index": plot_id},
                        type="number",
                        min=1,
                        max=n_dim,
                        step=1,
                        value=dim,
                        style={
                            "width": "60px",
                            "height": "40px",
                            "fontSize": "16px",
                            "borderRadius": "8px",
                            "border": "1px solid #ccc",
                            "marginLeft": "12px",
                            "padding": "0 10px",
                            "outline": "none",
                            "boxShadow": "none",
                        },
                    ),
                    html.Button(
                        "✖",
                        id={"type": "delete-plot-btn", "index": plot_id},
                        n_clicks=0,
                        style={
                            "marginLeft": "auto",
                            "marginRight": "10px",
                            "height": "32px",
                            "width": "32px",
                            "backgroundColor": "transparent",
                            "color": "#888",
                            "border": "none",
                            "borderRadius": "50%",
                            "cursor": "pointer",
                            "fontSize": "18px",
                            "lineHeight": "32px",
                            "textAlign": "center",
                        },
                    ),
                    html.Div(
                        id={"type": "delete-dummy", "index": plot_id},
                        style={"display": "none"},
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginBottom": "15px",
                },
            ),
            dcc.Graph(
                id={"type": "plot-graph", "index": plot_id},
                figure=figure,
                style={"marginBottom": "30px"},
            ),
            html.Div(
                id={"type": "plot-update-dummy", "index": plot_id},
                style={"display": "none"},
            ),
        ],
        style={
            "padding": "10px",
            "border": "1px solid #ddd",
            "borderRadius": "8px",
            "marginBottom": "20px",
            "backgroundColor": "#fafafa",
        },
    )
