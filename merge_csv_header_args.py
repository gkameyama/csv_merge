from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path


# Header-name ranges from the source CSV layouts.
COMMON_RANGE = ("l_userid", "SC22_2s2")
MAIN_RANGES = {
    "A": ("A1s1", "E2s15"),
    "B": ("AA1s1", "F4s7"),
    "C": ("AAA1_1s1", "G5s10"),
    "D": ("AAAA0", "H5s5"),
}
V_RANGE = ("V1c1", "V11s42")
A_TAIL_RANGE = ("P1", "R4c14")

# Output CSV encoding. Comment/uncomment these lines to switch encodings.
OUTPUT_ENCODING = "shift_jis"
# OUTPUT_ENCODING = "utf-8-sig"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge NHT2602 A/B/C/D CSV files by header-name ranges."
    )
    parser.add_argument("--a", required=True, help="Path to category A CSV file.")
    parser.add_argument("--b", required=True, help="Path to category B CSV file.")
    parser.add_argument("--c", required=True, help="Path to category C CSV file.")
    parser.add_argument("--d", required=True, help="Path to category D CSV file.")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output CSV path. Default: csv_merge_header_MMDDHHMM.csv",
    )
    return parser.parse_args()


def read_header(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return next(csv.reader(f))


def column_range(header: list[str], start: str, end: str) -> list[str]:
    try:
        start_index = header.index(start)
        end_index = header.index(end)
    except ValueError as exc:
        raise ValueError(f"Column range not found: {start} -> {end}") from exc

    if start_index > end_index:
        raise ValueError(f"Invalid range: {start} appears after {end}")

    return header[start_index : end_index + 1]


def validate_file(path: Path, category: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Category {category} file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Category {category} path is not a file: {path}")


def validate_columns(headers: dict[str, list[str]]) -> None:
    required_ranges = {
        "A": [COMMON_RANGE, MAIN_RANGES["A"], V_RANGE, A_TAIL_RANGE],
        "B": [COMMON_RANGE, MAIN_RANGES["B"], V_RANGE],
        "C": [COMMON_RANGE, MAIN_RANGES["C"], V_RANGE],
        "D": [COMMON_RANGE, MAIN_RANGES["D"], V_RANGE],
    }

    for category, ranges in required_ranges.items():
        header = headers[category]
        for start, end in ranges:
            column_range(header, start, end)


def build_header(headers: dict[str, list[str]]) -> list[str]:
    header = column_range(headers["A"], *COMMON_RANGE)
    header[0] = "SAMPLENUMBER"

    for category in ("A", "B", "C", "D"):
        header.extend(column_range(headers[category], *MAIN_RANGES[category]))

    header.extend(column_range(headers["A"], *V_RANGE))
    header.extend(column_range(headers["A"], *A_TAIL_RANGE))
    return header


def source_columns(category: str, headers: dict[str, list[str]]) -> list[str]:
    header = headers[category]
    columns = column_range(header, *COMMON_RANGE)
    columns.extend(column_range(header, *MAIN_RANGES[category]))
    columns.extend(column_range(header, *V_RANGE))

    if category == "A":
        columns.extend(column_range(header, *A_TAIL_RANGE))

    return columns


def destination_columns(category: str, output_header: list[str]) -> list[str]:
    columns = output_header[: len(column_range(output_header, "SAMPLENUMBER", COMMON_RANGE[1]))]
    columns.extend(column_range(output_header, *MAIN_RANGES[category]))
    columns.extend(column_range(output_header, *V_RANGE))

    if category == "A":
        columns.extend(column_range(output_header, *A_TAIL_RANGE))

    return columns


def samplenumber_sort_key(row: list[str]) -> tuple[int, float | str]:
    value = row[0].strip()
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)


def has_single_digit_a_column(row: list[str]) -> bool:
    value = row[0].strip()
    return len(value) == 1 and value.isdigit()


def default_output_file() -> Path:
    return Path(f"csv_merge_header_{datetime.now():%m%d%H%M}.csv")


def avoid_overwrite(path: Path) -> Path:
    if not path.exists():
        return path

    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def merge_csv(files: dict[str, Path], output_file: Path) -> None:
    for category, path in files.items():
        validate_file(path, category)

    headers = {category: read_header(path) for category, path in files.items()}
    validate_columns(headers)
    output_header = build_header(headers)
    output_index = {name: i for i, name in enumerate(output_header)}
    output_index["l_userid"] = output_index["SAMPLENUMBER"]
    output_rows: list[list[str]] = []

    for category in ("A", "B", "C", "D"):
        path = files[category]
        header = headers[category]
        input_index = {name: i for i, name in enumerate(header)}
        src_columns = source_columns(category, headers)
        dst_columns = destination_columns(category, output_header)

        with path.open("r", newline="", encoding="utf-8-sig") as in_f:
            reader = csv.reader(in_f)
            next(reader)

            for row in reader:
                out_row = [""] * len(output_header)
                for src, dst in zip(src_columns, dst_columns):
                    out_row[output_index[dst]] = row[input_index[src]]
                output_rows.append(out_row)

    output_rows.sort(key=samplenumber_sort_key)
    output_rows = [row for row in output_rows if not has_single_digit_a_column(row)]

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding=OUTPUT_ENCODING) as out_f:
        writer = csv.writer(out_f, lineterminator="\n")
        writer.writerow(output_header)
        writer.writerows(output_rows)


def main() -> None:
    args = parse_args()
    files = {
        "A": Path(args.a).expanduser().resolve(),
        "B": Path(args.b).expanduser().resolve(),
        "C": Path(args.c).expanduser().resolve(),
        "D": Path(args.d).expanduser().resolve(),
    }
    output_file = Path(args.output).expanduser().resolve() if args.output else default_output_file().resolve()
    output_file = avoid_overwrite(output_file)

    merge_csv(files, output_file)
    print(f"created: {output_file}")


if __name__ == "__main__":
    main()
