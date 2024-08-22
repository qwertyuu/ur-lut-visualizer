import dash
from dash import html, dcc
import os
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output


# Créer l'application Dash
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)


@app.callback(
    Output("test", "children"),
    Input("store-events", "data"),
)
def on_button_click(data):
    return "You have entered: \n{}".format(data)


def serve_layout():
    return dbc.Container(
        [
            html.H1("P5 dev"),
            html.Div(id="picker"),
            html.Button("Save", id="submit"),
            dcc.Store(id="store-events", data={}),
            html.Div(id="test"),
        ],
        fluid=True,
    )


app.layout = serve_layout
app.title = "P5dev"

# Exécuter l'application
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=bool(os.getenv("DEBUG", False)))
