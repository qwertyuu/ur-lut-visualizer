import json
import dash
from dash.dependencies import Input, Output
from dash import html, ALL
from royalur import LutAgent
from huggingface_hub import hf_hub_download
import pandas as pd
import io
import base64
from royalur import Game
from royalur.lut.board_encoder import SimpleGameStateEncoding
from royalur.model.player import PlayerType


REPO_ID = "sothatsit/RoyalUr"
FILENAME = "finkel.rgu"
filename = hf_hub_download(repo_id=REPO_ID, filename=FILENAME)
lut_player = LutAgent(filename)
lut = lut_player.lut
game = Game.create_finkel(pawns=7)
game_history = []
move_history = []
string = b""
if False:

    lut_df = pd.DataFrame(
        {
            "key": lut.keys_as_numpy(),
            "value": lut.values_as_numpy() / 65535,
        }
    )
    ax = lut_df.value.plot(
        kind="hist",
        title="Histogram of win probabilities of LUT",
        bins=500,
        figsize=(15, 5),
    )
    ax.axvline(lut_df.value.mean(), color="k", linestyle="dashed", linewidth=1)
    ax.set_xlabel("Win probability")
    ax.set_ylabel("Frequency")
    ax.axvline(lut_df.value.median(), color="r", linestyle="dashed", linewidth=1)

    # get png as base64
    buf = io.BytesIO()
    ax.figure.savefig(buf, format="png")
    buf.seek(0)
    string = base64.b64encode(buf.read())
    buf.close()

# Créer l'application Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True)

encoding = SimpleGameStateEncoding()


def get_lut_board_state(game: Game, compare_to_prob=None, history=False):
    string = game.get_board().to_string()
    light_player = game.get_light_player()
    dark_player = game.get_dark_player()
    string += f"\nLight: {light_player.piece_count}/{light_player.score} Dark: {dark_player.piece_count}/{dark_player.score}"
    current_state = game.get_current_state()
    value = lut_get(current_state)
    probability = value / 65535 * 100
    player_after_text = ""
    if compare_to_prob is not None:
        player_after_text = " after move"
    elif not history:
        if move_history:
            string += "\nLast Move: " + generate_move_text(len(move_history) - 1)

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
        return f"{string}\nWin prob: {light_string_proba}, {dark_string_proba}\nPlayer{player_after_text}: {current_state.get_winner().text_name} wins\n"
    return f"{string}\nWin prob: {light_string_proba}, {dark_string_proba}\nPlayer{player_after_text}: {current_state.get_turn().text_name}\n"


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


def is_back_disabled():
    return len(game_history) == 0


def generate_move_text(i):
    return f"#{i + 1} {move_history[i]}\n"


def generate_board_history():
    events = [
        (generate_move_text(i) if i != len(move_history) - 1 else "")
        + get_lut_board_state(game, history=True)
        for i, game in enumerate(game_history)
    ]
    events.reverse()
    return "\n".join(events)


# define callback for "Move" button
@app.callback(
    Output({"type": "move", "index": "back"}, "disabled"),
    Output("board", "children"),
    Output("available-moves", "children"),
    Output("board-history", "children"),
    Input({"type": "move", "index": ALL}, "n_clicks"),
    Input("reset", "n_clicks"),
    prevent_initial_call=True,
)
def on_button_click(n_clicks, reset_n_clicks):
    global game
    ctx = dash.callback_context
    print("on_button_click", ctx.triggered)
    if ctx.triggered[0]["prop_id"] == "reset.n_clicks":
        game = Game.create_finkel(pawns=7)
        move_history.clear()
        game_history.clear()
        return (
            is_back_disabled(),
            get_lut_board_state(game),
            generate_available_moves(game),
            generate_board_history(),
        )
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    button_id = json.loads(button_id)["index"]
    if button_id == "back":
        move_history.pop()
        game = game_history.pop()
        return (
            is_back_disabled(),
            get_lut_board_state(game),
            generate_available_moves(game),
            generate_board_history(),
        )
    game_history.append(game.copy())
    if "-" not in button_id:
        move_history.append("Switch player")
        dice = int(button_id)
        game.roll_dice(dice)
        return (
            is_back_disabled(),
            get_lut_board_state(game),
            generate_available_moves(game),
            generate_board_history(),
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
        is_back_disabled(),
        get_lut_board_state(game),
        generate_available_moves(game),
        generate_board_history(),
    )


code_style = {"whiteSpace": "pre-wrap", "font-family": "monospace"}


def generate_available_moves(game):
    new_components = []
    game_proba = lut_get(game.get_current_state()) / 65535 * 100
    for dice in range(5):
        new_components.append(
            html.Div(
                [
                    html.H3(f"Dice {dice}"),
                ]
            )
        )
        game_copy = game.copy()
        game_copy.roll_dice(dice)
        if not game_copy.is_waiting_for_move():
            new_components.append(
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
            continue
        moves = game_copy.find_available_moves()
        for i, move in enumerate(moves):
            game_move_copy = game_copy.copy()
            game_move_copy.make_move(move)
            new_components.append(
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
    return new_components


app.layout = html.Div(
    [
        # html.Img(src="data:image/png;base64," + string.decode("utf-8")),
        html.H1("Royal Game of Ur - LUT exploration"),
        html.Div(
            [
                html.Div(
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
                            "Go back to previous state",
                            id={"type": "move", "index": "back"},
                            n_clicks=0,
                            disabled=True,
                        ),
                        html.H2("Board history"),
                        html.Pre(
                            id="board-history",
                            children="",
                            style=code_style,
                        ),
                    ],
                    style={
                        "display": "inline-block",
                        "vertical-align": "top",
                        "width": "20%",
                    },
                ),
                html.Div(
                    [
                        html.H2("Available moves"),
                        html.Div(
                            id="available-moves",
                            children=generate_available_moves(game),
                        ),
                    ],
                    style={
                        "display": "inline-block",
                        "vertical-align": "top",
                        "width": "80%",
                        "overflow-x": "scroll",
                    },
                ),
            ]
        ),
    ]
)


# Exécuter l'application
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
