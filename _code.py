from tqdm import tqdm
from joblib import Parallel, delayed
import pandas as pd


def embarrassing2(contents, callback, n_jobs=8):
    with tqdm(total=len(contents)) as progress_bar:

        def uuu(q):
            ret = callback(q)
            progress_bar.update()
            return ret

        return Parallel(n_jobs=n_jobs, prefer="processes")(
            delayed(uuu)(i) for i in contents
        )


def do_the_thing(compute, n, to_convert):
    list_of_list = [to_convert[i : i + n] for i in range(0, len(to_convert), n)]
    insert_buffers = embarrassing2(list_of_list, compute, n_jobs=10)
    # flatten insert_buffers
    insert_buffers = [x for sublist in insert_buffers for x in sublist]
    # create dataframe
    return pd.DataFrame(
        insert_buffers, columns=["current_state", "next_state", "dice", "next_player"]
    )
