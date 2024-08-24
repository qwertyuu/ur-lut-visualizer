import json
import random
import dash
from dash.dependencies import Input, Output
from dash import html, ALL, dcc
from royalur import LutAgent
from huggingface_hub import hf_hub_download
import pandas as pd
from royalur import Game, Piece, PlayerState
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

    in ram:
    ix->
    * . * iy
    . . .  |
    . . .  v
    . * .
      .
      .
    * . *
    . . .
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
    parts = []
    current_state = game.get_current_state()
    value = lut_get(current_state)
    probability = value / 65535 * 100

    light_string_proba = f"○ {probability:.2f}%"
    if compare_to_prob is not None:
        proba_diff = probability - compare_to_prob
        if proba_diff > 0:
            light_string_proba += f" (+{proba_diff:.2f}%)"
        else:
            light_string_proba += f" ({proba_diff:.2f}%)"

    dark_string_proba = f"● {100-probability:.2f}%"
    if compare_to_prob is not None:
        proba_diff = 100 - probability - (100 - compare_to_prob)
        if proba_diff > 0:
            dark_string_proba += f" (+{proba_diff:.2f}%)"
        else:
            dark_string_proba += f" ({proba_diff:.2f}%)"

    def nice_to_ascii(nice: str):
        return "●" if nice == "Dark" else "○"

    after_board_parts = []
    if current_state.is_finished():
        parts.append(f"\nWin prob: {light_string_proba}, {dark_string_proba}")
        after_board_parts.append(
            f"\n{nice_to_ascii(current_state.get_winner().text_name)} wins"
        )
    else:
        parts.append(f"\nWin prob: {light_string_proba}, {dark_string_proba}")
        after_board_parts.append(
            f"\n{nice_to_ascii(current_state.get_turn().text_name)}'s turn"
        )

    parts.append(nicer_ascii)
    parts.extend(after_board_parts)
    light_player = game.get_light_player()
    dark_player = game.get_dark_player()
    parts.append(
        f"○: {light_player.piece_count} pieces, {light_player.score} score\n●: {dark_player.piece_count} pieces, {dark_player.score} score"
    )

    return "\n".join(parts)


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


@app.callback(
    Output({"type": "move", "index": "back"}, "disabled"),
    Output("board", "children"),
    Output("available-moves", "children"),
    Input({"type": "move", "index": ALL}, "n_clicks"),
    Input("reset", "n_clicks"),
    Input("session_id", "data"),
    Input("store-events", "data"),
    prevent_initial_call=True,
)
def on_button_click(n_clicks, reset_n_clicks, session_id, store_data):
    game = get_session_game(session_id)
    move_history = get_session_move_history(session_id)
    game_history = get_session_game_history(session_id)
    ctx = dash.callback_context
    if "store-events.data" == ctx.triggered[0]["prop_id"]:
        move_history.clear()
        game_history.clear()
        new_game = Game.create_finkel(pawns=7)
        board = new_game.get_board()
        for light_pawn_pos in store_data["L"]["board_positions"]:
            board.set_by_indices(
                light_pawn_pos[0],
                light_pawn_pos[1],
                Piece(PlayerType.LIGHT, light_pawn_pos[2]),
            )
        for dark_pawn_pos in store_data["D"]["board_positions"]:
            board.set_by_indices(
                dark_pawn_pos[0],
                dark_pawn_pos[1],
                Piece(PlayerType.DARK, dark_pawn_pos[2]),
            )

        lp = new_game.get_current_state().light_player
        new_game.get_current_state()._light_player = PlayerState(
            lp.player, store_data["L"]["left"], store_data["L"]["score"]
        )
        dp = new_game.get_current_state().dark_player
        new_game.get_current_state()._dark_player = PlayerState(
            dp.player, store_data["D"]["left"], store_data["D"]["score"]
        )
        new_game.get_current_state()._turn = (
            PlayerType.DARK if store_data["current_player"] == "D" else PlayerType.LIGHT
        )
        game = set_game(session_id, new_game)
        return (
            is_back_disabled(game_history),
            get_lut_board_state(game),
            generate_available_moves(game),
        )
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
    "font-family": "DejaVu Sans Mono",
    "font-size": "12px",
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
                        dbc.Button(
                            "Switch player",
                            id={"type": "move", "index": f"{dice}"},
                            n_clicks=0,
                            size="sm",
                            color="secondary",
                        ),
                        html.P(
                            get_lut_board_state(
                                game_copy,
                                game_proba,
                            ),
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
                            dbc.Button(
                                move.describe(),
                                id={"type": "move", "index": f"{dice}-{i}"},
                                n_clicks=0,
                                color="secondary",
                                size="sm",
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


# Callback to toggle modal visibility
@app.callback(
    [Output("input-modal", "is_open"), Output("store-events-out", "children")],
    [Input("open-modal", "n_clicks"), Input("save-changes", "n_clicks")],
    [dash.State("input-modal", "is_open"), dash.State("session_id", "data")],
)
def toggle_modal(open_clicks, close_clicks, is_open, session_id):
    game = get_session_game(session_id)
    store_data = {
        "L": {
            "board_positions": [],
            "left": 0,
            "score": 0,
        },
        "D": {
            "board_positions": [],
            "left": 0,
            "score": 0,
        },
        "current_player": "L",
    }
    board = game.get_board()

    for ix in range(board._width):
        for iy in range(board._height):
            if board._shape.contains_indices(ix, iy):
                piece = board.get_by_indices(ix, iy)
                if piece:
                    store_data[piece.owner.character]["board_positions"].append(
                        [ix, iy]
                    )
    current_state = game.get_current_state()
    lp = current_state.light_player
    store_data["L"]["left"] = lp.piece_count
    store_data["L"]["score"] = lp.score
    dp = current_state.dark_player
    store_data["D"]["left"] = dp.piece_count
    store_data["D"]["score"] = dp.score

    if current_state.is_finished():
        if current_state.get_winner() == PlayerType.DARK:
            store_data["current_player"] = "D"
        else:
            store_data["current_player"] = "L"
    else:
        if current_state.get_turn() == PlayerType.DARK:
            store_data["current_player"] = "D"
        else:
            store_data["current_player"] = "L"

    if open_clicks or close_clicks:
        return not is_open, json.dumps(store_data)
    return is_open, json.dumps(store_data)


def serve_layout():
    session_id = str(random.randint(0, 1000000))
    game = get_session_game(session_id)
    return dbc.Container(
        [
            html.H1("Royal Game of Ur - LUT exploration"),
            html.P("Under the Finkel ruleset - More rulesets coming soon!"),
            dcc.Markdown(
                "This explorer is [open source](https://github.com/qwertyuu/ur-lut-visualizer)! Come help me make it better!"
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle("Enter your game state using the picker"),
                        id="modal-header",
                    ),
                    dbc.ModalBody(
                        [
                            html.Div(id="picker"),
                            html.Div(id="store-events-out", style={"display": "none"}),
                        ],
                        id="modal-body",
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Close",
                                id="save-changes",
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="input-modal",
                is_open=False,
                size="lg",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("Current board"),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        "State editor",
                                        id="open-modal",
                                        n_clicks=0,
                                        color="primary",
                                    ),
                                    dbc.Button(
                                        "New game",
                                        id="reset",
                                        n_clicks=0,
                                        color="secondary",
                                    ),
                                    dbc.Button(
                                        "Undo last move",
                                        id={"type": "move", "index": "back"},
                                        n_clicks=0,
                                        disabled=True,
                                        color="secondary",
                                    ),
                                ]
                            ),
                            html.P(
                                id="board",
                                children=get_lut_board_state(game),
                                style=code_style,
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
            dcc.Store(id="store-events", data={}),
        ],
        fluid=True,
    )


app.layout = serve_layout
app.title = "RGU - LUT explorer"

# Exécuter l'application
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=bool(os.getenv("DEBUG", False)))
