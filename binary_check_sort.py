file_to_check = "lut_transition_merge_sort/round_8/output_0.data"

with open(file_to_check, "rb", buffering=1000000000) as f:
    row = f.read(10)
    last_int = row[:4]
    while row:
        row = f.read(10)
        if row:
            int_ = row[:4]
            if int_ < last_int:
                print(f"File {file_to_check} is not sorted")
                break
            last_int = int_
    else:
        print(f"File {file_to_check} is sorted")
