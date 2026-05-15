from __future__ import annotations

import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "NHT2602_data_all.csv"

FILES = {
    "A": BASE_DIR / "NHT2602_A0.csv",
    "B": BASE_DIR / "NHT2602_B0.csv",
    "C": BASE_DIR / "NHT2602_C0.csv",
    "D": BASE_DIR / "NHT2602_D0.csv",
}


def read_header(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return next(csv.reader(f))


def column_range(header: list[str], start: str, end: str) -> list[str]:
    start_index = header.index(start)
    end_index = header.index(end)
    if start_index > end_index:
        raise ValueError(f"Invalid range: {start} appears after {end}")
    return header[start_index : end_index + 1]


def build_layout(headers: dict[str, list[str]]) -> list[str]:
    common = column_range(headers["A"], "l_userid", "SC22.22")
    common[0] = "SAMPLENUMBER"

    a_main = column_range(headers["A"], "A1.1", "E2.15")
    b_main = column_range(headers["B"], "AA1.1", "F4.7")
    c_main = column_range(headers["C"], "AAA1.101", "G5.10")
    d_main = column_range(headers["D"], "AAAA0", "H5.5")
    v_common = column_range(headers["A"], "V1_1", "V11.42")
    a_tail = column_range(headers["A"], "P1", "R4_14")

    return common + a_main + b_main + c_main + d_main + v_common + a_tail


def source_columns(category: str, headers: dict[str, list[str]]) -> list[str]:
    header = headers[category]
    columns = column_range(header, "l_userid", "SC22.22")

    if category == "A":
        columns += column_range(header, "A1.1", "E2.15")
    elif category == "B":
        columns += column_range(header, "AA1.1", "F4.7")
    elif category == "C":
        columns += column_range(header, "AAA1.101", "G5.10")
    elif category == "D":
        columns += column_range(header, "AAAA0", "H5.5")
    else:
        raise ValueError(f"Unknown category: {category}")

    columns += column_range(header, "V1_1", "V11.42")

    if category == "A":
        columns += column_range(header, "P1", "R4_14")

    return columns


def samplenumber_sort_key(row: list[str]) -> tuple[int, float | str]:
    value = row[0].strip()
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)


def merge_csv() -> None:
    headers = {category: read_header(path) for category, path in FILES.items()}
    output_header = build_layout(headers)
    output_index = {name: i for i, name in enumerate(output_header)}
    output_index["l_userid"] = output_index["SAMPLENUMBER"]
    output_rows: list[list[str]] = []

    for category, path in FILES.items():
        header = headers[category]
        input_index = {name: i for i, name in enumerate(header)}
        columns = source_columns(category, headers)

        with path.open("r", newline="", encoding="utf-8-sig") as in_f:
            reader = csv.reader(in_f)
            next(reader)

            for row in reader:
                out_row = [""] * len(output_header)
                for column in columns:
                    out_row[output_index[column]] = row[input_index[column]]
                output_rows.append(out_row)

    output_rows.sort(key=samplenumber_sort_key)

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as out_f:
        writer = csv.writer(out_f, lineterminator="\n")
        writer.writerow(output_header)
        writer.writerows(output_rows)


if __name__ == "__main__":
    merge_csv()
    print(f"created: {OUTPUT_FILE}")
