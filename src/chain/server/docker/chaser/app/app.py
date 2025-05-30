import asyncio
import logging
import os
import uuid
from pathlib import Path
from threading import Thread

import dash
from chaser.server import chaser_grpc_server
from dash import Dash, Input, Output, State, html
from dash.dependencies import MATCH
from flask import request

from src.engine import (
    add_experiment,
    add_run,
    add_tag,
    check_prj_id,
    delete_plot_state,
    generate_plot,
    get_plot_state,
    list_experiments,
    list_metrics,
    list_runs_hierarchy,
    push_all_to_s3,
    save_plot_state,
)
from src.layout import get_layout, get_run_list
from src.plot import plot_card

logger = logging.getLogger(__name__)
DATA_DIR = Path("/data/experiments")

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Chaser Dashboard"
app.layout = get_layout()


def start_grpc_background() -> None:
    def start() -> None:
        asyncio.run(chaser_grpc_server(host="0.0.0.0", port=14000))

    Thread(target=start, daemon=True).start()


start_grpc_background()


##########################################
# リスト更新系
##########################################
@app.callback(
    Output("experiment-dropdown", "options"),
    Input("reload-experiment-list", "n_intervals"),
)
def update_experiment_list(n_intervals: int) -> list:
    return [{"label": exp["name"], "value": exp["id"]} for exp in list_experiments()]


@app.callback(
    Output("run-list-container", "children"),
    Input("experiment-dropdown", "value"),
    Input("selected-run", "data"),
)
def update_run_list(experiment_id: int, selected_run: str):
    if not experiment_id:
        return "Please select an experiment."
    hierarchy = list_runs_hierarchy(experiment_id)
    return get_run_list(hierarchy, selected_run)


@app.callback(
    Output("metrics-list-container", "children"),
    Input("selected-run", "data"),
    State("experiment-dropdown", "value"),
)
def update_metric_list(selected_run: str, experiment_id: int):
    if not selected_run or not experiment_id:
        return "No run selected."
    metrics = list_metrics(experiment_id, selected_run)
    if not metrics:
        return "No metrics found."
    return html.Ul(
        [html.Li(metric, style={"marginBottom": "4px"}) for metric in metrics],
        style={"paddingLeft": "16px", "margin": 0},
    )


@app.callback(
    Output("selected-run", "data"),
    Input("run-radio", "value"),
)
def update_selected_run(value: str) -> str:
    return value


##########################################
# ボタン
##########################################
@app.callback(
    Output("add-plot-btn", "disabled"),
    Input("selected-run", "data"),
    Input("experiment-dropdown", "value"),
)
def enable_add_plot_btn(selected_run: str, experiment_id: str) -> bool:
    if not selected_run or not experiment_id:
        return True
    metrics = list_metrics(experiment_id, selected_run)
    return len(metrics) == 0


@app.callback(
    Output("add-plot-btn", "style"),
    Input("add-plot-btn", "disabled"),
)
def update_button_style(is_disabled):
    base_style = {
        "marginTop": "10px",
        "padding": "10px 16px",
        "fontSize": "15px",
        "border": "none",
        "borderRadius": "8px",
    }
    if is_disabled:
        base_style.update({"backgroundColor": "#cccccc", "color": "#666666", "cursor": "not-allowed"})
    else:
        base_style.update({"backgroundColor": "#007bff", "color": "white", "cursor": "pointer"})
    return base_style


##########################################
# 図
##########################################
# 図一覧を DB から取得して描画
@app.callback(
    Output("plots-container", "children"),
    Input("selected-run", "data"),
    State("experiment-dropdown", "value"),
)
def update_all_plots(selected_run, experiment_id):
    if not selected_run or not experiment_id:
        return []
    try:
        saved_plots = get_plot_state(selected_run)
    except Exception:
        logger.exception("Failed to load plot state")
        return []
    all_metrics = list_metrics(experiment_id, selected_run)
    children = []
    for plot_id, plot in saved_plots.items():
        metrics_list = plot.get("metrics", [])
        if not metrics_list:
            continue
        metric = metrics_list[0].get("metric")[0]  # list
        options = metrics_list[0].get("option", {})  # dict
        n_dim = options.get("n_dim", 1)
        dim = options.get("dim", 1)
        figure = generate_plot(experiment_id, selected_run, metric, n_dim, dim)
        if metric:
            children.append(
                plot_card(
                    plot_id=plot_id,
                    figure=figure,
                    all_metrics=all_metrics,
                    metric=metric,
                    n_dim=n_dim,
                    dim=dim,
                )
            )
    return children


# プロットの内容を更新（metric or dimが変化したとき）
@app.callback(
    Output({"type": "plot-update-dummy", "index": MATCH}, "children"),
    [
        Input({"type": "metric-dropdown", "index": MATCH}, "value"),
        Input({"type": "dim-input", "index": MATCH}, "value"),
    ],
    [
        State({"type": "plot-graph", "index": MATCH}, "id"),
        State("experiment-dropdown", "value"),
        State("selected-run", "data"),
    ],
    prevent_initial_call=True,
)
def update_plot(selected_metric, selected_dim, plot_info, experiment_id, selected_run):
    if not (plot_info and experiment_id and selected_run):
        raise dash.exceptions.PreventUpdates
    try:
        plot_id = plot_info["index"]
        save_plot_state(experiment_id, selected_run, plot_id, selected_metric, selected_dim)
    except Exception:
        logger.exception("Failed to update plot state")
    return ""


# プロットの追加／削除操作
@app.callback(
    Output("add-dummy", "children"),
    Input("add-plot-btn", "n_clicks"),
    State("selected-run", "data"),
    State("experiment-dropdown", "value"),
    prevent_initial_call=True,
)
def add_plot(n_clicks, selected_run, experiment_id):
    if not selected_run or not experiment_id:
        raise dash.exceptions.PreventUpdate
    try:
        plot_id = str(uuid.uuid4())
        save_plot_state(experiment_id, selected_run, plot_id)
    except Exception:
        logger.exception("Failed to add plot")
    return ""


@app.callback(
    Output({"type": "delete-dummy", "index": MATCH}, "children"),
    Input({"type": "delete-plot-btn", "index": MATCH}, "n_clicks"),
    State({"type": "delete-plot-btn", "index": MATCH}, "id"),
    State("selected-run", "data"),
    prevent_initial_call=True,
)
def delete_plot(n_clicks, btn_id, selected_run):
    if not selected_run or not n_clicks:
        raise dash.exceptions.PreventUpdate
    plot_id = btn_id["index"]
    try:
        delete_plot_state(selected_run, plot_id)
    except Exception:
        logger.exception("Failed to delete plot")
    return ""


##########################################
# API
##########################################


@server.route("/start_run/<prj_id>/<experiment_id>/<run_uuid>", methods=["POST"])
def start_run(prj_id: str, experiment_id: str, run_uuid: str) -> dict:
    check_prj_id(prj_id)
    parent = request.form.get("parent")
    exp_name = request.form.get("experiment_name")
    run_name = request.form.get("run_name")
    dir_path = DATA_DIR / experiment_id / run_uuid
    dir_path.mkdir(exist_ok=True, parents=True)
    add_experiment(experiment_id, exp_name)
    add_run(run_uuid, run_name, experiment_id)
    if parent is not None:
        add_tag(run_uuid, "mlflow.parentRunId", parent)
    return {"status": "ok"}


@server.route("/end_run/<prj_id>/<experiment_id>/<run_uuid>", methods=["POST"])
def end_run(prj_id: str, experiment_id: str, run_uuid: str) -> dict:
    check_prj_id(prj_id)
    dir_path = DATA_DIR / experiment_id / run_uuid
    push_all_to_s3(dir_path)
    return {"status": "ok"}


@server.route("/metric/<prj_id>/<experiment_id>/<run_uuid>", methods=["POST"])
def save_metric(prj_id: str, experiment_id: str, run_uuid: str) -> dict:
    check_prj_id(prj_id)
    key = request.form.get("key")
    dim = request.form.get("dim")
    vec_file = request.files["value"]
    dir_path = DATA_DIR / experiment_id / run_uuid
    metric_path = dir_path / f"{key}.bin"
    meta_path = dir_path / f"{key}.meta"
    with open(metric_path, "ab") as f:
        f.write(vec_file.read())
    if not meta_path.exists():
        with open(meta_path, "w") as f:
            f.write(str(dim))
    return {"status": "ok"}


@server.get("/grpc")
def get_grpc_port():
    return {"port": os.getenv("GRPC_PORT")}


##########################################
# API
##########################################


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8150)
