import sys
import csv

def read_csv(filename):
    records = []
    with open(filename, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            records.append(row)
    return records

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    filename = "../resources/" + sys.argv[1]
    records = read_csv(filename)
    for record in records:
        print(",".join(record))
