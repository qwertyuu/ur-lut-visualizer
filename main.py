from royalur import LutAgent
from huggingface_hub import hf_hub_download
import pandas as pd

REPO_ID = "sothatsit/RoyalUr"
FILENAME = "finkel.rgu"
filename = hf_hub_download(repo_id=REPO_ID, filename=FILENAME)
lut_player = LutAgent(filename)
lut = lut_player.lut

pd.DataFrame(
    {
        "key": lut.keys_as_numpy(),
        "value": lut.values_as_numpy(),
    }
)
