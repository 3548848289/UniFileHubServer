import sys
import csv

def update_csv(filename, row, col, new_value):
    rows = []

    # 读取CSV文件内容
    with open(filename, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file)
        for line in csv_reader:
            rows.append(line)

    # 更新指定单元格的值
    if 0 <= row < len(rows) and 0 <= col < len(rows[row]):
        rows[row][col] = new_value
    else:
        print("Invalid row or column index")
        return

    # 写回CSV文件
    with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(rows)

    print(f"Updated row {row}, column {col} with new value: {new_value}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python update_csv.py <filename> <row> <col> <new_value>")
        sys.exit(1)

    filename = sys.argv[1]
    row = int(sys.argv[2]) + 1
    col = int(sys.argv[3])
    new_value = sys.argv[4]

    update_csv(filename, row, col, new_value)
