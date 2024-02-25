import dash
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from dash import dcc, html

# Créer l'application Dash
app = dash.Dash(__name__)

# Définir la disposition de l'application
app.layout = html.Div(
    [
        dcc.Input(id="my-input", type="text"),
        html.Button(id="submit-button", children="Soumettre"),
        dcc.Graph(id="my-graph"),
    ]
)


# Appeler la fonction de mise à jour du graphique lorsque la valeur de l'entrée est modifiée
@app.callback(
    Output("my-graph", "figure"),
    [Input("submit-button", "n_clicks")],
    [State("my-input", "value")],
)
def update_output(n_clicks, input_value):
    # Créer un graphique avec Plotly
    figure = go.Figure(
        data=[
            go.Bar(x=["Taux de clics", "Impressions"], y=[int(input_value or 0), 100])
        ]
    )
    return figure


# Exécuter l'application
if __name__ == "__main__":
    app.run(debug=True)
