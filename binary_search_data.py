import os
import datetime


class BinarySearchData:
    def __init__(self, file):
        self.file = file
        self.file_size = os.path.getsize(file)
        self.amt_of_rows = self.file_size // 10

    def search_any(self, search_value):
        self.tries = 0
        search_value = search_value.to_bytes(4, "big")
        with open(self.file, "rb") as f:
            start = 0
            end = self.amt_of_rows
            middle = (start + end) // 2
            f.seek(middle * 10)
            row = f.read(10)
            int_ = row[:4]
            while int_ != search_value and start < end:
                if search_value < int_:
                    end = middle
                else:
                    start = middle + 1
                middle = (start + end) // 2
                f.seek(middle * 10)
                row = f.read(10)
                int_ = row[:4]
                self.tries += 1
            if int_ == search_value:
                from_index = int.from_bytes(int_, "big")
                to_index = int.from_bytes(row[4:8], "big")
                dice = int.from_bytes(row[8:9], "big")
                next_player = int.from_bytes(row[9:10], "big", signed=True)
                return middle, {"from_index": from_index, "to_index": to_index, "dice": dice, "next_player": next_player}
            return None, None

    def search_first(self, search_value):
        self.tries = 0
        search_value = search_value.to_bytes(4, "big")
        with open(self.file, "rb") as f:
            start = 0
            end = self.amt_of_rows
            middle = (start + end) // 2
            f.seek(middle * 10)
            row = f.read(10)
            int_ = row[:4]
            while int_ != search_value and start < end:
                if search_value < int_:
                    end = middle
                else:
                    start = middle + 1
                middle = (start + end) // 2
                f.seek(middle * 10)
                row = f.read(10)
                int_ = row[:4]
                self.tries += 1
            if int_ == search_value:
                # make sure to find the first occurrence
                while middle > 0:
                    f.seek((middle - 1) * 10)
                    row = f.read(10)
                    int_ = row[:4]
                    if int_ != search_value:
                        break
                    middle -= 1
                f.seek(middle * 10)
                row = f.read(10)
                int_ = row[:4]
                from_index = int.from_bytes(int_, "big")
                to_index = int.from_bytes(row[4:8], "big")
                dice = int.from_bytes(row[8:9], "big")
                next_player = int.from_bytes(row[9:10], "big", signed=True)
                return middle, {"from_index": from_index, "to_index": to_index, "dice": dice, "next_player": next_player}
            return None, None

    def search_all(self, search_value):
        self.tries = 0
        search_value = search_value.to_bytes(4, "big")
        with open(self.file, "rb") as f:
            start = 0
            end = self.amt_of_rows
            middle = (start + end) // 2
            f.seek(middle * 10)
            row = f.read(10)
            int_ = row[:4]
            while int_ != search_value and start < end:
                if search_value < int_:
                    end = middle
                else:
                    start = middle + 1
                middle = (start + end) // 2
                f.seek(middle * 10)
                row = f.read(10)
                int_ = row[:4]
                self.tries += 1
            if int_ == search_value:
                # make sure to find the first occurrence
                while middle > 0:
                    f.seek((middle - 1) * 10)
                    row = f.read(10)
                    int_ = row[:4]
                    if int_ != search_value:
                        break
                    middle -= 1
                f.seek(middle * 10)
                row = f.read(10)
                int_ = row[:4]
                # accumulate all occurrences
                first_middle = middle
                results = []
                while int_ == search_value:
                    from_index = int.from_bytes(int_, "big")
                    to_index = int.from_bytes(row[4:8], "big")
                    dice = int.from_bytes(row[8:9], "big")
                    next_player = int.from_bytes(row[9:10], "big", signed=True)
                    results.append({"from_index": from_index, "to_index": to_index, "dice": dice, "next_player": next_player})
                    middle += 1
                    f.seek(middle * 10)
                    row = f.read(10)
                    int_ = row[:4]
                return first_middle, results
            return None, None


starttime = datetime.datetime.now()

file = "lut_transition_merge_sort/round_8/output_0.data"

search_value = 138113

search = BinarySearchData(file)
print(search.search_first(search_value))
print("Took", datetime.datetime.now() - starttime)
print("Tries:", search.tries)

print(search.search_any(search_value))
print("Took", datetime.datetime.now() - starttime)
print("Tries:", search.tries)

print(search.search_all(search_value))
print("Took", datetime.datetime.now() - starttime)
print("Tries:", search.tries)