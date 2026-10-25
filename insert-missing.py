
#!/usr/bin/env python3
# coding: utf-8

import csv
import os
import fitz  # pip install pymupdf
import yaml


# ------------------------------------------------------
# Read configuration
# ------------------------------------------------------

CONFIG_FILE = "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

PDF_DIR = config["insert_missing_dir"]
CSV_FILE = os.path.join(PDF_DIR, config["insertions_csv"])

# ------------------------------------------------------
# Resolve paths relative to the config.yaml directory
# ------------------------------------------------------

CONFIG_DIR = os.path.dirname(os.path.abspath(CONFIG_FILE))

if not os.path.isabs(PDF_DIR):
    PDF_DIR = os.path.join(CONFIG_DIR, PDF_DIR)

if not os.path.isabs(CSV_FILE):
    CSV_FILE = os.path.join(CONFIG_DIR, CSV_FILE)

# If the CSV filename is relative to PDF_DIR, use that directory.
if not os.path.isabs(config["insertions_csv"]):
    CSV_FILE = os.path.join(PDF_DIR, config["insertions_csv"])


# ------------------------------------------------------
# Insert missing pages
# ------------------------------------------------------

if not os.path.isfile(CSV_FILE):
    raise FileNotFoundError(f"Insertions CSV not found: {CSV_FILE}")

with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, skipinitialspace=True)

    required_columns = {"filename-a", "filename-b", "X", "Y"}

    if not reader.fieldnames or not required_columns.issubset(
        {name.strip() for name in reader.fieldnames}
    ):
        raise ValueError(
            "insertions.csv must contain these columns: "
            "filename-a, filename-b, X, Y"
        )

    for row in reader:
        try:
            file_a = os.path.join(
                PDF_DIR, row["filename-a"].strip()
            )
            file_b = os.path.join(
                PDF_DIR, row["filename-b"].strip()
            )

            X = int(row["X"])
            Y = int(row["Y"])

            output_file = (
                os.path.splitext(file_a)[0] + "-mod.pdf"
            )

            if not os.path.isfile(file_a):
                raise FileNotFoundError(
                    f"PDF A not found: {file_a}"
                )

            if not os.path.isfile(file_b):
                raise FileNotFoundError(
                    f"PDF B not found: {file_b}"
                )

            with fitz.open(file_a) as a, fitz.open(file_b) as b:

                # X is a one-based page number in PDF B.
                if not 1 <= X <= len(b):
                    raise ValueError(
                        f"Invalid page X={X} in {file_b}; "
                        f"PDF has {len(b)} pages"
                    )

                # Y is a zero-based insertion position in PDF A.
                if not 0 <= Y <= len(a):
                    raise ValueError(
                        f"Invalid insertion position Y={Y}; "
                        f"PDF A has {len(a)} pages"
                    )

                a.insert_pdf(
                    b,
                    from_page=X - 1,
                    to_page=X - 1,
                    start_at=Y
                )

                a.save(
                    output_file,
                    garbage=4,
                    deflate=True
                )

            print(f"SUCCESS: {output_file}")

        except Exception as e:
            filename = row.get("filename-a", "<unknown>").strip()
            print(f"FAILED: {filename}: {e}")

