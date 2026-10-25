#!/usr/bin/env python3

import os
import fitz  # pip install pymupdf

directory = "./exam/exam-data/final-scans"
total_pages = 0

for filename in sorted(os.listdir(directory)):
    filepath = os.path.join(directory, filename)

    if os.path.isfile(filepath) and filename.lower().endswith(".pdf"):
        try:
            with fitz.open(filepath) as pdf:
                pages = pdf.page_count
                total_pages += pages
                print(f"{filename}: {pages} pages")
        except Exception as e:
            print(f"{filename}: ERROR - {e}")

print(f"\nTotal pages: {total_pages}")