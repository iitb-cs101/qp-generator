#!/usr/bin/env python3
# coding: utf-8

# pyzbar needs an additional library 
# sudo apt-get install libzbar0  - Linux (Ubuntu/Debian)
# brew install zbar - macOS
# pip install pyzbar fuzzywuzzy python-Levenshtein

# import pytesseract
# from fuzzywuzzy import fuzz

import os
import fitz
from PIL import Image
import pandas as pd
# uncomment for mac zbar
# os.environ["DYLD_LIBRARY_PATH"] = "/opt/homebrew/opt/zbar/lib"

from pyzbar.pyzbar import decode
import qrtools 
import pytesseract

import yaml



#------------------------------
# Open and read the Yaml file
#------------------------------
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
scanned_pdf_folder_path = config['raw_scan_folder']
output_directory        = config['scanned_output_dir']
expected_pages          = config['expected_pages']

#----------------------------------------------
# Read student data if you wish to cross check
#----------------------------------------------
form_file               = config['student_data']
reg_nos                 = []

if os.path.exists(form_file):
    form_data = pd.read_csv(form_file)
    reg_nos = form_data["Roll No."].tolist()
else:
    print( 'No student data available! No checks on the validity of the read roll numbers!' )

#------------------------------------------------------
# Multi_decode
#------------------------------------------------------

def my_decode( image ):
    decoded_objects = decode(image)
    if decoded_objects: return decoded_objects
    # image.save( f"{output_directory}/tmp.png" )
    # ---------------------------
    # QR tools
    # ---------------------------
    # qr = qrtools.QR()
    # qr.decode( f"{output_directory}/tmp.png" )
    # print(qr.data)
    # exit()
    return None

#------------------------------------------------------
# Reading qr code from scanned pages
#------------------------------------------------------
def read_qr_code(page,input_file="",page_num=0):
    page_width = page.rect.width
    page_height = page.rect.height

    for repeat in [0,180]:
        if repeat != 0: page.set_rotation(180)
        # ----------------------------------------
        # Clipping the page to reduce qr scan area 
        # ----------------------------------------
        crop_width = 180 #140 # 240
        crop_height = 200 #130 # 130
        crop_x = page_width - crop_width
        crop_y = 0
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1, 1), clip=fitz.Rect(crop_x, crop_y, crop_x + crop_width-20, crop_y + crop_height-20))
        pil_image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        pil_image = pil_image.convert("L") # cropped image containing QR code

        # ----------------------------------------
        # Try rotation of 0 90 180 270   30 120 210 300  60 150 240 330 degrees 
        # ----------------------------------------
        pil_image_orig = pil_image.copy()
        if repeat == 0: top_right = pil_image_orig.copy()
        for j in range(0,90): # 0 30 60
            for i in range(0,4): # 0 90 180 270
                decoded_objects = my_decode(pil_image)
                if decoded_objects: break
                pil_image = pil_image_orig.rotate(90*(i+1)+j*1, Image.BILINEAR, expand = 1)
            if decoded_objects: break
        if decoded_objects: break
    # if j > 0 or i > 0: print(f'Decoding retried: {j*4+i+1}')

    # ----------------------------------------
    # Saving failure cases for inspection.
    # ----------------------------------------
    if not decoded_objects:
        print(f'Failed to scan!')
        top_right.save( f"{output_directory}/failed_page_{input_file}_{page_num}_grayscale.png" )

    page.set_rotation(0)
    return decoded_objects

#------------------------------------------------------
# Main code to read and sort raw scanned answerbooks
#------------------------------------------------------

files = os.listdir(scanned_pdf_folder_path)
pdf_files = [f for f in files if f.endswith('.pdf')]
if not os.path.exists(output_directory):
    import pathlib
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True) 

sorted_documents = {}
unidentified_documents = []
repeated_lists = {}

for pdf_file in pdf_files:
    scanned_pdf_path = os.path.join(scanned_pdf_folder_path, pdf_file)
    if os.path.exists(scanned_pdf_path):
        pdf_document = fitz.open(scanned_pdf_path)
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            # Reading qr on each page
            decoded_objects = read_qr_code(page,pdf_file,page_num)
            if decoded_objects:
                qr_data = decoded_objects[0].data.decode('utf-8')
                roll_no, page_n = qr_data.rsplit('_')
                if len(reg_nos) > 0 and (not roll_no in reg_nos):
                    print(f'Unexpected {roll_no} is found!')
                if not roll_no in sorted_documents:
                    sorted_documents[roll_no] = {}
                if int(page_n) in sorted_documents[roll_no]:
                    if not f"{roll_no}_{int(page_n)}" in repeated_lists:
                        repeated_lists[f"{roll_no}_{int(page_n)}"] = [sorted_documents[roll_no][int(page_n)]]
                    repeated_lists[f"{roll_no}_{int(page_n)}"].append((pdf_document,page_num))
                    print(f"{roll_no}_{int(page_n)} found again")
                else:
                    sorted_documents[roll_no][int(page_n)] = (pdf_document,page_num)
            else:
                unidentified_documents.append((pdf_document,page_num)) 

# with open("Bunch-V-identified.txt", "w") as f:
#     for roll_no, pages in sorted_documents.items():
#         for page_num, (pdf_document, page_n) in pages.items():
#             f.write(f"Roll No: {roll_no}, Page {page_num}, Document: {pdf_document}, Page Number: {page_n}\n")

# with open("Bunch-V-unidentified_docs.txt", "w") as f:
#     for pdf_document, page_num in unidentified_documents:
#         f.write(f"Document: {pdf_document}, Page Number: {page_num}\n")


reg_nos_set = set(reg_nos)
#----------------------------------
# Save sorted pages for each Roll No
#----------------------------------
for roll_no, pages in sorted_documents.items():
    pdf_writer = fitz.open()
    sorted_pages = sorted(pages.items(), key=lambda x: x[0])
    found_pages = []
    for idx, (doc,page_num) in sorted_pages:
        pdf_writer.insert_pdf(doc, from_page= page_num, to_page= page_num)
        found_pages.append(idx)
        
    output_path = os.path.join(output_directory, f"{roll_no}.pdf")
    pdf_writer.save(output_path)
    if len(sorted_pages) != expected_pages:
        not_found = []
        for pnum in range(0,expected_pages):
            if not pnum in found_pages:
                not_found.append(pnum)
        print(f'Saving scanned answerbook for {roll_no} with {len(sorted_pages)} pages {not_found}')
    reg_nos_set.remove(roll_no)
    pdf_writer.close()

if len(reg_nos_set) > 0:
    print('No scanned pdf found for student(s):', reg_nos_set)
    
#---------------------------------------------
# Dump repeated pages into a single document
#---------------------------------------------
if repeated_lists:
    pdf_writer = fitz.open()
    page_count = 0
    for _, page_pairs in repeated_lists.items():
        for (doc,page_num) in page_pairs:
            pdf_writer.insert_pdf( doc, from_page= page_num, to_page= page_num )
            page_count += 1
    output_path = os.path.join(output_directory, "repeated-pages-documents.pdf")
    pdf_writer.save(output_path)
    pdf_writer.close()
    print(f"{page_count} pages are found to be repetitive, saving them in {output_path}")

#---------------------------------------------
# Dump unidentified pages into single document
#---------------------------------------------
if unidentified_documents:
    pdf_writer = fitz.open()
    for doc,page_num in unidentified_documents:
        pdf_writer.insert_pdf(doc, from_page= page_num, to_page= page_num) 
    output_path = os.path.join(output_directory, "unidentified-documents.pdf")
    pdf_writer.save(output_path)
    print(f"{len(unidentified_documents)} pages remained unidentified, saving them in {output_path}")
    pdf_writer.close()
    pdf_document.close()
else:
    print("No unidentified document!")

