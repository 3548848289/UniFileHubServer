import sys
import csv
def read_csv(filename):
    records = []
    with open(filename, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader)
        for row in csv_reader:
            c3 = row[0]
            add_all = row[1]
            gender = row[2]
            student_id = row[3]
            dormitory = row[4]
            records.append((c3, add_all, gender, student_id, dormitory))
    return records

def format_records(records):
    formatted = []
    for record in records:
        formatted.append(f"('{record[0]}', '{record[1]}', '{record[2]}', '{record[3]}', '{record[4]}')")
    return formatted

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    filename = "../resouses/" + sys.argv[1]
    records = read_csv(filename)
    formatted_records = format_records(records)
    for record in formatted_records:
        print(record)
