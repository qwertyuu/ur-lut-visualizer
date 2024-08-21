import json
import random
import dash
from dash.dependencies import Input, Output
from dash import html, ALL, dcc
from royalur import LutAgent
from huggingface_hub import hf_hub_download
import pandas as pd
from royalur import Game
from royalur.lut.board_encoder import SimpleGameStateEncoding
from royalur.model.player import PlayerType
import os
import dash_bootstrap_components as dbc


REPO_ID = "sothatsit/RoyalUr"
FILENAME = "finkel.rgu"
filename = hf_hub_download(
    repo_id=REPO_ID, filename=FILENAME, cache_dir=os.getenv("HF_CACHE_DIR", None)
)
lut_player = LutAgent(filename)
lut = lut_player.lut
data_by_session = {}


def get_session_game(session_id):
    if session_id not in data_by_session:
        init_session(session_id)
    return data_by_session[session_id]["game"]


def init_session(session_id):
    data_by_session[session_id] = {
        "game": Game.create_finkel(pawns=7),
        "game_history": [],
        "move_history": [],
        "init_date": pd.Timestamp.now(),
    }


def set_game(session_id, game):
    data_by_session[session_id]["game"] = game
    return game


def get_session_game_history(session_id):
    if session_id not in data_by_session:
        init_session(session_id)
    return data_by_session[session_id]["game_history"]


def get_session_move_history(session_id):
    if session_id not in data_by_session:
        init_session(session_id)
    return data_by_session[session_id]["move_history"]


# Créer l'application Dash
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

encoding = SimpleGameStateEncoding()


def to_nicer_ascii(game: Game):
    board = game.get_board()
    """
     _ _ _ _     _ _
    |*|_|_|_|_ _|*|_|
    |_|_|_|*|_|_|_|_|
    |*|_|_|_|   |*|_|
    """
    """
    Writes the contents of this board into a String, where
    each column is separated by a delimiter.
    """
    rosette_spots = [
        (0, 0),
        (0, 6),
        (1, 3),
        (2, 0),
        (2, 6),
    ]
    builder = list(" _ _ _ _     _ _\n|")
    for ix in range(board._width):
        if ix > 0:
            builder.append("\n|")

        for iy in range(board._height):
            if board._shape.contains_indices(ix, iy):
                piece = board.get_by_indices(ix, iy)
                if piece:
                    builder.append("○" if piece.owner.character == "L" else "●")
                else:
                    if (ix, iy) in rosette_spots:
                        builder.append("☆")
                    else:
                        builder.append("_")
                builder.append("|")
            else:
                if ix == 0:
                    if iy == 5:
                        builder.append("_|")
                    else:
                        builder.append("_ ")
                else:
                    if iy == 5:
                        builder.append(" |")
                    else:
                        builder.append("  ")

    return "".join(builder)


def get_lut_board_state(game: Game, compare_to_prob=None):
    nicer_ascii = to_nicer_ascii(game)
    string = nicer_ascii + "\n"
    light_player = game.get_light_player()
    dark_player = game.get_dark_player()
    string += f"\nRemaining pawn & score: Light ({light_player.piece_count} / {light_player.score}), Dark ({dark_player.piece_count} / {dark_player.score})"
    current_state = game.get_current_state()
    value = lut_get(current_state)
    probability = value / 65535 * 100
    player_after_text = "Current player"
    if compare_to_prob is not None:
        player_after_text = "Player after move"

    light_string_proba = f"Light {probability:.2f}% "
    if compare_to_prob is not None:
        proba_diff = probability - compare_to_prob
        if proba_diff > 0:
            light_string_proba += f" (+{proba_diff:.2f}%)"
        else:
            light_string_proba += f" ({proba_diff:.2f}%)"

    dark_string_proba = f"Dark {100-probability:.2f}% "
    if compare_to_prob is not None:
        proba_diff = 100 - probability - (100 - compare_to_prob)
        if proba_diff > 0:
            dark_string_proba += f" (+{proba_diff:.2f}%)"
        else:
            dark_string_proba += f" ({proba_diff:.2f}%)"
    if current_state.is_finished():
        return f"{string}\nWin prob: {light_string_proba}, {dark_string_proba}\n{player_after_text}: {current_state.get_winner().text_name} wins\n"
    return f"{string}\nWin prob: {light_string_proba}, {dark_string_proba}\n{player_after_text}: {current_state.get_turn().text_name}\n"


def lut_get(current_state):
    inverted = False
    if current_state.is_finished():
        if current_state.get_winner() == PlayerType.DARK:
            value = 0
        else:
            value = 65535
    else:
        if (
            not current_state.is_finished()
            and current_state.get_turn() != PlayerType.LIGHT
        ):
            # invert the state because
            # the LUT is only for the light player
            current_state = current_state.copy_inverted()
            assert current_state.get_turn() == PlayerType.LIGHT
            inverted = True
        state = encoding.encode_game_state(current_state)
        value = lut.lookup(0, state)
    if inverted:
        value = 65535 - value
    return value


def is_back_disabled(game_history):
    return len(game_history) == 0


def generate_move_text(i, move_history):
    return f"#{i + 1} {move_history[i]}\n"


# define callback for "Move" button
@app.callback(
    Output({"type": "move", "index": "back"}, "disabled"),
    Output("board", "children"),
    Output("available-moves", "children"),
    Input({"type": "move", "index": ALL}, "n_clicks"),
    Input("reset", "n_clicks"),
    Input("session_id", "data"),
    prevent_initial_call=True,
)
def on_button_click(n_clicks, reset_n_clicks, session_id):
    game = get_session_game(session_id)
    move_history = get_session_move_history(session_id)
    game_history = get_session_game_history(session_id)
    ctx = dash.callback_context
    if ctx.triggered[0]["prop_id"] == "reset.n_clicks":
        init_session(session_id)
        game = get_session_game(session_id)
        move_history = get_session_move_history(session_id)
        game_history = get_session_game_history(session_id)
        return (
            is_back_disabled(game_history),
            get_lut_board_state(game),
            generate_available_moves(game),
        )
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    button_id = json.loads(button_id)["index"]
    if button_id == "back":
        move_history.pop()
        game = set_game(session_id, game_history.pop())
        return (
            is_back_disabled(game_history),
            get_lut_board_state(game),
            generate_available_moves(game),
        )
    game_history.append(game.copy())
    if "-" not in button_id:
        move_history.append("Switch player")
        dice = int(button_id)
        game.roll_dice(dice)
        return (
            is_back_disabled(game_history),
            get_lut_board_state(game),
            generate_available_moves(game),
        )
    dice, move_index = button_id.split("-")
    dice = int(dice)
    move_index = int(move_index)
    game.roll_dice(dice)
    moves = game.find_available_moves()
    move = moves[move_index]
    move_history.append(move.describe())
    game.make_move(move)
    return (
        is_back_disabled(game_history),
        get_lut_board_state(game),
        generate_available_moves(game),
    )


code_style = {
    "whiteSpace": "pre-wrap",
    "font-family": "monospace",
    "font-size": "14px",
    "margin-right": "14px",
}


def generate_available_moves(game):
    new_components = []
    game_proba = lut_get(game.get_current_state()) / 65535 * 100
    for dice in range(5):
        dice_components = []
        game_copy = game.copy()
        game_copy.roll_dice(dice)
        if not game_copy.is_waiting_for_move():
            dice_components.append(
                html.Div(
                    [
                        html.Button(
                            "Switch player",
                            id={"type": "move", "index": f"{dice}"},
                            n_clicks=0,
                        ),
                        html.P(
                            get_lut_board_state(
                                game_copy,
                                game_proba,
                            ),
                            # monospace font for preformatted text
                            style=code_style,
                        ),
                    ],
                    style={"display": "inline-block"},
                )
            )
        else:
            moves = game_copy.find_available_moves()
            for i, move in enumerate(moves):
                game_move_copy = game_copy.copy()
                game_move_copy.make_move(move)
                dice_components.append(
                    html.Div(
                        [
                            html.Button(
                                move.describe(),
                                id={"type": "move", "index": f"{dice}-{i}"},
                                n_clicks=0,
                            ),
                            html.P(
                                get_lut_board_state(game_move_copy, game_proba),
                                style=code_style,
                            ),
                        ],
                        style={"display": "inline-block"},
                    )
                )
        new_components.append(
            html.Div(
                [
                    html.H3(f"Roll of {dice}"),
                    *dice_components,
                ],
                className="dice",
                style={"border-bottom": "1px solid grey"},
            )
        )
    return new_components


def serve_layout():
    session_id = str(random.randint(0, 1000000))
    game = get_session_game(session_id)
    return dbc.Container(
        [
            html.H1("Royal Game of Ur - LUT exploration"),
            html.P("Under the Finkel ruleset - More rulesets coming soon!"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("Current board"),
                            html.Button(
                                "Reset",
                                id="reset",
                                n_clicks=0,
                            ),
                            html.P(
                                id="board",
                                children=get_lut_board_state(game),
                                style=code_style,
                            ),
                            html.Button(
                                "Undo move",
                                id={"type": "move", "index": "back"},
                                n_clicks=0,
                                disabled=True,
                            ),
                        ],
                        style={
                            "vertical-align": "top",
                        },
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.H2("Available moves"),
                            html.Div(
                                id="available-moves",
                                children=generate_available_moves(game),
                            ),
                        ],
                        style={
                            "vertical-align": "top",
                            "overflow-x": "scroll",
                        },
                        md=9,
                    ),
                ]
            ),
            dcc.Store(id="session_id", data=session_id),
        ],
        fluid=True,
    )


app.layout = serve_layout
app.title = "RGU - LUT explorer"

# Exécuter l'application
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=bool(os.getenv("DEBUG", False)))
