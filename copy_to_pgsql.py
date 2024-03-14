import pyarrow.parquet as pq
import psycopg2
import tqdm
from multiprocessing import Pool

# Replace these with your own values
parquet_file = "boardstates.parquet"
postgresql_conn_str = "postgresql://postgres:mysecretpassword@localhost/postgres"
table_name = "boardstates"


def create_table(cursor):
    cursor.execute(
        """
        CREATE TABLE boardstates (
            lut_value float8 NULL,
            lut_index int4 NULL,
            light_score int4 NULL,
            dark_score int4 NULL,
            boardstate varchar NULL,
            a1 int4 NULL,
            b1 int4 NULL,
            c1 int4 NULL,
            a2 int4 NULL,
            b2 int4 NULL,
            c2 int4 NULL,
            a3 int4 NULL,
            b3 int4 NULL,
            c3 int4 NULL,
            a4 int4 NULL,
            b4 int4 NULL,
            c4 int4 NULL,
            b5 int4 NULL,
            b6 int4 NULL,
            a7 int4 NULL,
            b7 int4 NULL,
            c7 int4 NULL,
            a8 int4 NULL,
            b8 int4 NULL,
            c8 int4 NULL,
            light_piece_count int4 NULL,
            dark_piece_count int4 NULL,
            light_piece_left_to_play int4 NULL,
            dark_piece_left_to_play int4 NULL
        );"""
    )


def insert_data(batch):
    conn = psycopg2.connect(postgresql_conn_str)
    cursor = conn.cursor()

    df = batch.to_pandas()
    values_str = []
    for row in df.values.tolist():
        values_str.append("(" + ", ".join([f"'{str(x)}'" for x in row]) + ")")

    cursor.execute(
        "INSERT INTO {} ({}) VALUES {}".format(
            table_name,
            ", ".join(batch.schema.names),
            ", ".join(values_str),
        ),
    )
    # print(f"Inserted {len(batch)} rows")

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    # Create a PostgreSQL connection
    conn = psycopg2.connect(postgresql_conn_str)
    cursor = conn.cursor()

    create_table(cursor)
    conn.commit()
    cursor.close()
    conn.close()
    total = 0
    # Get the schema of the Parquet file
    with pq.ParquetFile(parquet_file) as pf:
        total = pf.metadata.num_rows

    # Use a multiprocessing Pool
    with Pool(processes=5) as pool:
        inserted = 0
        # Read the Parquet file in batches and apply insert_data to each batch
        batch_size = 200000
        for _ in tqdm.tqdm(
            pool.imap_unordered(
                insert_data,
                pq.ParquetFile(parquet_file).iter_batches(batch_size=batch_size),
            ),
            total=total // batch_size,
        ):
            inserted += batch_size

    # Close the connection
