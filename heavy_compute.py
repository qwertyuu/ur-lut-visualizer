from royalur import Board
from royalur.model import StandardBoardShape, Piece, PlayerState
from royalur.model.player import PlayerType
from royalur.rules.state import WaitingForRollGameState
from royalur.lut.board_encoder import SimpleGameStateEncoding
import duckdb
import pandas as pd
from tqdm import tqdm
from joblib import Parallel, delayed
from multiprocessing import Pool


char_to_player = {
    "L": PlayerType.LIGHT,
    "D": PlayerType.DARK,
}
common_path = [1, 4, 7, 10, 13, 16, 19, 22]
light_path = [9, 6, 3, 0, *common_path, 21, 18]
dark_path = [11, 8, 5, 2, *common_path, 23, 20]
rosette_index = [0, 2, 10, 18, 20]

light_path_map = {e: i for i, e in enumerate(light_path)}
dark_path_map = {e: i for i, e in enumerate(dark_path)}
CENTER_ROSETTE_POS = 10
LIGHT_TOP_ROSETTE_POS = 0
LIGHT_BOTTOM_ROSETTE_POS = 18
path_len = 14

light_rosette_index = [
    LIGHT_TOP_ROSETTE_POS,
    CENTER_ROSETTE_POS,
    LIGHT_BOTTOM_ROSETTE_POS,
]

char_to_path = {
    "L": light_path,
    "D": dark_path,
}


def formatted(boardstr):
    parts = []
    for i in range(0, len(boardstr), 3):
        parts.append(boardstr[i : i + 3])
    return "\n".join(parts)


def overwrite(s, char, index):
    return s[:index] + char + s[index + 1 :]


def compute_available_moves(boardstr, light_score, light_pawns, dark_score, dark_pawns):
    possible_moves = [
        (
            boardstr,
            light_score,
            light_pawns,
            dark_score,
            dark_pawns,
            0,
            2,
            False,
        )
    ]
    can_add_pawn = light_pawns > 0
    # contains the index of the boardstr where the pawn is along with the position in path
    active_light_pawns = [
        (i, light_path.index(i)) for i, char in enumerate(boardstr) if char == "L"
    ]
    for dice in range(1, 5):
        if can_add_pawn and boardstr[light_path[dice - 1]] == ".":
            play_boardstr_index = light_path[dice - 1]
            new_boardstr = overwrite(boardstr, "L", play_boardstr_index)
            possible_moves.append(
                (
                    new_boardstr,
                    light_score,
                    light_pawns - 1,
                    dark_score,
                    dark_pawns,
                    dice,
                    1 if play_boardstr_index == LIGHT_TOP_ROSETTE_POS else 2,
                    False,
                )
            )
        for (
            active_light_pawn_boardstr_index,
            active_light_pawn_path_index,
        ) in active_light_pawns:
            if active_light_pawn_path_index + dice == path_len:
                # one more point
                new_boardstr = overwrite(
                    boardstr, ".", active_light_pawn_boardstr_index
                )
                new_light_score = light_score + 1
                possible_moves.append(
                    (
                        new_boardstr,
                        new_light_score,
                        light_pawns,
                        dark_score,
                        dark_pawns,
                        dice,
                        2,
                        new_light_score == 7,
                    )
                )
            elif active_light_pawn_path_index + dice < path_len:
                play_boardstr_index = light_path[active_light_pawn_path_index + dice]
                # we play over a D pawn that is not on the center rosette
                if (
                    boardstr[play_boardstr_index] == "D"
                    and play_boardstr_index != CENTER_ROSETTE_POS
                ):
                    new_boardstr = overwrite(
                        boardstr, ".", active_light_pawn_boardstr_index
                    )
                    new_boardstr = overwrite(new_boardstr, "L", play_boardstr_index)
                    possible_moves.append(
                        (
                            new_boardstr,
                            light_score,
                            light_pawns,
                            dark_score,
                            dark_pawns + 1,
                            dice,
                            2,
                            False,
                        )
                    )
                elif boardstr[play_boardstr_index] == ".":
                    # we play over a free spot
                    new_boardstr = overwrite(
                        boardstr, ".", active_light_pawn_boardstr_index
                    )
                    new_boardstr = overwrite(new_boardstr, "L", play_boardstr_index)
                    possible_moves.append(
                        (
                            new_boardstr,
                            light_score,
                            light_pawns,
                            dark_score,
                            dark_pawns,
                            dice,
                            1 if play_boardstr_index in light_rosette_index else 2,
                            False,
                        )
                    )

    return possible_moves


def embarrassing2(contents, callback, n_jobs=8):
    with tqdm(total=len(contents)) as progress_bar:

        def uuu(q):
            ret = callback(q)
            progress_bar.update()
            return ret

        r = Parallel(n_jobs=n_jobs, prefer="processes")(
            delayed(uuu)(i) for i in contents
        )
        return r


def do_query(query):
    with duckdb.connect("local2.db") as con:
        return con.execute(query).fetchdf()


def do_query_obj(query):
    with duckdb.connect("local2.db") as con:
        return con.execute(query).fetchall()


do_query("DROP TABLE IF EXISTS lut_transition;")
do_query(
    "CREATE TABLE lut_transition(current_state INTEGER, next_state INTEGER, dice INTEGER, next_player INTEGER);"
)


limit = 1000000
offset = 0
encoding = SimpleGameStateEncoding()


def compute(list_of_tup):
    b = Board(StandardBoardShape())
    insert_buffer = []
    for (
        board_state,
        light_score,
        light_piece_left_to_play,
        dark_score,
        dark_piece_left_to_play,
        lut_index,
    ) in list_of_tup:
        insert_buffer.append((lut_index, lut_index, 0, 2))
        moves = compute_available_moves(
            board_state,
            light_score,
            light_piece_left_to_play,
            dark_score,
            dark_piece_left_to_play,
        )
        for (
            boardstr,
            light_score,
            light_pawns,
            dark_score,
            dark_pawns,
            dice,
            active_player,
            light_won,
        ) in moves:
            if dice == 0:
                continue

            for i in range(len(boardstr)):
                state = boardstr[i]
                p = None
                if state != ".":
                    p = Piece(char_to_player[state], path_map[state][i])
                b._pieces[i] = p
            light_player_state = PlayerState(PlayerType.LIGHT, light_pawns, light_score)
            dark_player_state = PlayerState(PlayerType.DARK, dark_pawns, dark_score)
            gs = WaitingForRollGameState(
                b,
                light_player_state,
                dark_player_state,
                PlayerType.LIGHT,
            )
            lut_state = encoding.encode_game_state(gs)
            if light_won:
                insert_buffer.append((lut_index, lut_state, dice, -1))
            else:
                insert_buffer.append((lut_index, lut_state, dice, active_player))
    return insert_buffer


path_map = {
    "L": light_path_map,
    "D": dark_path_map,
}


n_jobs = 16
#chunks = (n_jobs * 3)
n = 10000  # chunk row size


if __name__ == "__main__":
    while True:
        to_convert = do_query_obj(
            f"""
            SELECT boardstate, light_score, light_piece_left_to_play, dark_score, dark_piece_left_to_play, lut_index
            FROM boardstate_lut_expanded_int_values 
            WHERE light_score < 7 AND dark_score < 7 
            LIMIT {limit} OFFSET {offset}
            """
        )
        if len(to_convert) == 0:
            break
        offset += limit
        print(offset)
        list_of_list = [to_convert[i : i + n] for i in range(0, len(to_convert), n)]
        #insert_buffers = []
        with duckdb.connect("local2.db") as con:
            with Pool(n_jobs) as p:
                with tqdm(total=len(list_of_list)) as pbar:
                    for r in p.imap_unordered(compute, list_of_list):
                        #insert_buffers += r
                        #print("Inserting...")
                        df = pd.DataFrame(
                            r,
                            columns=["current_state", "next_state", "dice", "next_player"],
                        )
                        con.execute("INSERT INTO lut_transition SELECT * FROM df")
                        #print("Done")
                        pbar.update()
            # insert_buffers = p.map(compute, list_of_list)
        # flatten insert_buffers
        # create dataframe
        
        #break

# profile.disable()
# profile.print_stats()
