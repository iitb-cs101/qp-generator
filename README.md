# Question Paper Generator

Utility to generate customized question papers (PDF) files for each student using a sample PDF and a seating list. Each generated PDF includes student-specific details like roll number, name, room, seat, and QR code.



## Structure

```
.
├── requirements.txt
├── bulk-printing.ps1
├── generate-qp.py
├── read-scanned-answerbooks.py
└── exam/
    ├── config.yaml
    ├── Makefile
    ├── seating.csv
    └── exam.pdf   # (to be provided by user)
```


## Seating File Format

File: `exam/seating.csv`

```csv
Roll No.,Name,Room No.,Seat No.
25B99999,Student-name,LA002-YELLOW,A11
```

* Each row represents one student
* This data will be displayed/embedded into the generated PDFs


## Sample/Master Question Paper

* File: `exam/<filename.pdf>`
* The input PDF must be placed inside this `exam/` folder

## Configuration

All configuration is handled via: ```exam/config.yaml```

### Generating Question Paper
* `student_data`: The filename of the CSV that contains the seating arrangement of the students
* `input_question_paper`: The input PDF (sample/master question paper)
* `output_question_paper_dir`: The output directory for the generated PDFs

### Collating Answer Books from Raw Scans
* `raw_scan_folder`: Directory where the RAW scanned answer books are stored
* `scanned_output_dir`: Directory where the processed scanned answer books will be stored
* `expected_pages`: Number of pages in the question paper (for validation purposes)

## How to Run
* Navigate to the exam folder: ```cd exam```
* To generate question paper: ```make qp```
* To collate RAW scans per student: ```make read-scanned```

## Requirements
* Python 3.8+
* See requirements.txt