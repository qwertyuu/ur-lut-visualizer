# list files in the binary_sorted_lut_transition directory

import os

# Path to the directory
path = "lut_transition_merge_sort/round_7"
output_path = "lut_transition_merge_sort"

# List files in the directory
files = os.listdir(path)

# sort the files taking numbers in the file name into account
files.sort(key=lambda f: int("".join(filter(str.isdigit, f))))

"""
logic:
- pull row from each file
- compare first 4 bytes of each row
- push the row with the smaller integer to the output file
- pull the next row from the file that had the smaller integer
- repeat until all rows are processed
"""

round = 8

buffer_size = 10000000
# iterate in steps of 2 files
for i in range(0, len(files), 2):
    # check that both files exist
    if i + 1 >= len(files):
        print(f"File {files[i]} does not have a pair")
        # write the file to the output directory as is
        with open(f"{path}/{files[i]}", "rb", buffering=buffer_size) as f, open(
            f"{output_path}/round_{round}/output_{i}.data", "wb", buffering=buffer_size
        ) as output:
            row = f.read(10)
            while row:
                output.write(row)
                row = f.read(10)
        continue
    print(f"Processing files {files[i]} and {files[i+1]}")

    # open the files
    with open(f"{path}/{files[i]}", "rb", buffering=buffer_size) as f1, open(
        f"{path}/{files[i+1]}", "rb", buffering=buffer_size
    ) as f2:
        # read the first 4 bytes from each file
        row1 = f1.read(10)
        row2 = f2.read(10)

        # open the output file
        with open(
            f"{output_path}/round_{round}/output_{i}.data", "wb", buffering=buffer_size
        ) as output:
            # iterate until the end of the file
            while row1 and row2:
                int1 = row1[:4]
                int2 = row2[:4]
                # compare the first 4 bytes
                if int1 < int2:
                    # write the row from the first file to the output file
                    output.write(row1)
                    # read the next row from the first file
                    row1 = f1.read(10)
                    int1 = row1[:4]
                else:
                    # write the row from the second file to the output file
                    output.write(row2)
                    # read the next row from the second file
                    row2 = f2.read(10)
                    int2 = row2[:4]

            # write the remaining rows from the first file to the output file
            while row1:
                output.write(row1)
                row1 = f1.read(10)

            # write the remaining rows from the second file to the output file
            while row2:
                output.write(row2)
                row2 = f2.read(10)
