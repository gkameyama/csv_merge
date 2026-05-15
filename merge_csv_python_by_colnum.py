from __future__ import annotations

import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "NHT2602_data_all_by_colnum.csv"

FILES = {
    "A": BASE_DIR / "NHT2602_A0.csv",
    "B": BASE_DIR / "NHT2602_B0.csv",
    "C": BASE_DIR / "NHT2602_C0.csv",
    "D": BASE_DIR / "NHT2602_D0.csv",
}

# 1-based column ranges from the source CSV layouts.
COMMON_RANGE = (1, 3637)
MAIN_RANGES = {
    "A": (3638, 9971),
    "B": (3638, 7182),
    "C": (3638, 9168),
    "D": (3638, 7256),
}
V_RANGES = {
    "A": (9972, 10233),
    "B": (7183, 7444),
    "C": (9169, 9430),
    "D": (7257, 7518),
}
A_TAIL_RANGE = (10234, 10362)


def read_header(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return next(csv.reader(f))


def one_based_range(start: int, end: int) -> range:
    if start > end:
        raise ValueError(f"Invalid range: {start} > {end}")
    return range(start - 1, end)


def pick(values: list[str], start: int, end: int) -> list[str]:
    return [values[i] for i in one_based_range(start, end)]


def build_header(headers: dict[str, list[str]]) -> list[str]:
    header = pick(headers["A"], *COMMON_RANGE)
    header[0] = "SAMPLENUMBER"

    for category in ("A", "B", "C", "D"):
        header.extend(pick(headers[category], *MAIN_RANGES[category]))

    header.extend(pick(headers["A"], *V_RANGES["A"]))
    header.extend(pick(headers["A"], *A_TAIL_RANGE))
    return header


def source_indexes(category: str) -> list[int]:
    indexes = list(one_based_range(*COMMON_RANGE))
    indexes.extend(one_based_range(*MAIN_RANGES[category]))
    indexes.extend(one_based_range(*V_RANGES[category]))

    if category == "A":
        indexes.extend(one_based_range(*A_TAIL_RANGE))

    return indexes


def destination_indexes(category: str, main_offsets: dict[str, int], v_offset: int, a_tail_offset: int) -> list[int]:
    indexes = list(range(COMMON_RANGE[1]))
    indexes.extend(range(main_offsets[category], main_offsets[category] + (MAIN_RANGES[category][1] - MAIN_RANGES[category][0] + 1)))
    indexes.extend(range(v_offset, v_offset + (V_RANGES[category][1] - V_RANGES[category][0] + 1)))

    if category == "A":
        indexes.extend(range(a_tail_offset, a_tail_offset + (A_TAIL_RANGE[1] - A_TAIL_RANGE[0] + 1)))

    return indexes


def samplenumber_sort_key(row: list[str]) -> tuple[int, float | str]:
    value = row[0].strip()
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)


def merge_csv() -> None:
    headers = {category: read_header(path) for category, path in FILES.items()}
    output_header = build_header(headers)

    main_offsets: dict[str, int] = {}
    cursor = COMMON_RANGE[1]
    for category in ("A", "B", "C", "D"):
        main_offsets[category] = cursor
        cursor += MAIN_RANGES[category][1] - MAIN_RANGES[category][0] + 1

    v_offset = cursor
    cursor += V_RANGES["A"][1] - V_RANGES["A"][0] + 1
    a_tail_offset = cursor
    output_rows: list[list[str]] = []

    for category, path in FILES.items():
        src_indexes = source_indexes(category)
        dst_indexes = destination_indexes(category, main_offsets, v_offset, a_tail_offset)

        with path.open("r", newline="", encoding="utf-8-sig") as in_f:
            reader = csv.reader(in_f)
            next(reader)

            for row in reader:
                out_row = [""] * len(output_header)
                for src, dst in zip(src_indexes, dst_indexes):
                    out_row[dst] = row[src]
                output_rows.append(out_row)

    output_rows.sort(key=samplenumber_sort_key)

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as out_f:
        writer = csv.writer(out_f, lineterminator="\n")
        writer.writerow(output_header)
        writer.writerows(output_rows)


if __name__ == "__main__":
    merge_csv()
    print(f"created: {OUTPUT_FILE}")
