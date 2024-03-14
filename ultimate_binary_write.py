import pyarrow.parquet as pq

parquet_file = pq.ParquetFile('lut_transition.parquet')

batch_size = 10000000

for i, batch in enumerate(parquet_file.iter_batches(batch_size)):
    print(f"Processing batch {i} ({(i * batch_size) / parquet_file.metadata.num_rows * 100:.2f}%)")
    batch = batch.sort_by([('current_state', 'ascending'), ('dice', 'ascending')])
    current_state = batch["current_state"]
    next_state = batch["next_state"]
    dice = batch["dice"]
    next_player = batch["next_player"]

    """
    Write on disk using the following format:
    32bit current (unsigned)
    32bit next (unsigned)
    4bit dice (unsigned)
    4bit next_player (signed)
    """

    with open(f'binary_sorted_lut_transition/lut_transition_{batch_size * i}.data', 'wb') as f:
        for i in range(len(current_state)):
            f.write(current_state[i].as_py().to_bytes(4, 'big'))
            f.write(next_state[i].as_py().to_bytes(4, 'big'))
            f.write(dice[i].as_py().to_bytes(1, 'big'))
            f.write(next_player[i].as_py().to_bytes(1, 'big', signed=True))
            # debug
            #print(current_state[i].as_py(), next_state[i].as_py(), dice[i].as_py(), next_player[i].as_py())
            #break

    #break
