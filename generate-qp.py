#!/usr/bin/env python3
# coding: utf-8

# Author: Prof. Ashutosh Gupta

import io
import os
import fitz
import qrcode
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter # version 3.something is needed
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image
import math
from joblib import Parallel, delayed
from tqdm import tqdm
import yaml
import sys

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

student_data = config['student_data'             ]
qp_pdf       = config['input_question_paper'     ]
student_dir  = config['output_question_paper_dir']

path_to_script = sys.argv
# print_script = "/".join( path_to_script[0].split('/')[:-1] ) + "/bulk-printing.ps1"
print_script = "../bulk-printing.ps1"



os.system(f'mkdir -p {student_dir}/qp')
os.system(f'cp {print_script} {student_dir}/qp')

# -----------------------------------------------
# Read student data
#------------------------------------------------
df = pd.read_csv(student_data)

#------------------------------------------------------
# QR code insertion handling
#------------------------------------------------------

# Function to generate a qr Code
def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# Function to add QR code to each page of a PDF
def add_qr_code_to_pdf(pdf, qr_data, room, seat):
    # ---------------------------------------------------
    # Inset a page if total number of pages is odd number
    # ---------------------------------------------------
    # if pdf.getNumPages() % 2 == 1:
    #     pdf.addBlankPage(width=612, height=792)

    output_pdf = PdfWriter()

    for page_num in range(len(pdf.pages)):
        
        page        = pdf.pages[page_num]
        page_width  = page.mediabox[2]
        page_height = page.mediabox[3]
        # print(page_width)
        # print(page_height)

        qr_img = generate_qr_code(qr_data+'_'+str(page_num))

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
        can.setFont(psfontname ='Times-Roman', size = 20)

        if page_num != 0:
            can.drawString(60,page_height - 40 , seat+'-'+room+'-'+qr_data)

        # hide pre-existing page numbers
        # can.setFillColorRGB(255, 255, 255)
        # can.setStrokeColorRGB(255, 255, 255)
        # can.rect(200, 0, 300, 80, stroke=1, fill=1) 

        # draw new page numbers (in order)
        # can.setStrokeColorRGB(0, 0, 0)
        # can.setFillColorRGB(0, 0, 0)
        # if page_num != 0:
        #     can.drawString(page_width/2 - 4, page_height - 40 ,str(page_num + 1))

        # Draw box for the scores
        can.rect(  page_width - 250, page_height - 100, 80, 70)
        can.setFont(psfontname ='Times-Roman', size = 11)
        can.drawString( page_width - 245, page_height - 25 , 'Marks obtained')

        # add qr code
        qr_img_temp = io.BytesIO()
        qr_img.save(qr_img_temp, format='PNG')
        can.drawImage(ImageReader(qr_img_temp), page_width - 150 , page_height - 100, width = 90, height = 90)
        can.save()
        packet.seek(0)

        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]

        page.merge_page(overlay_page)
        output_pdf.add_page(page)
    
    return output_pdf

#------------------------------------------------------
# Insert student details
#------------------------------------------------------

def fill_student_details(pdf_path, fields, details):
    assert( len(fields) == len(details) )
    
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)

    for i in range(len(fields)):
        text_instances = page.search_for(fields[i])
        if len(text_instances) == 0:
            print(f"{fields[i]} is not found in the pdf!")
        else:
            inst = text_instances[0] 
            rect = fitz.Rect(inst.x1-140, inst.y0+5, inst.x1+ len(details[i]) + 200, inst.y1 + 20) 
            rc = page.insert_textbox(rect, details[i], fontsize = 12,
                                     fontname = "Times-Roman",     
                                     fontfile = None,              
                                     align = 1)

    doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()

     
#------------------------------------------------------
#  Process each student 
#------------------------------------------------------

fields = ["Name", "Roll No.","Seat"]

qp_path = qp_pdf #os.path.join( paper_dir, qp_pdf )
if not os.path.exists(qp_path):
    print(f"{qp_path} is missing")
    exit()

def runner( pair ):
    index = pair[0]
    row   = pair[1]

    # ------------------------------
    # Collect data from application
    # ------------------------------
    reg_no      = row['Roll No.']
    full_name   = row['Name']
    seat        = row["Seat No."]
    room        = row["Room No."]

    # truncate full name
    if len(full_name) > 20: full_name = full_name[0:20]

    output_pdf = PdfWriter()
    
    # --------------------------------------
    # Insert question paper in the student file
    # --------------------------------------
    qp_pdf = PdfReader(open(qp_path, 'rb'))
    output_pdf.append_pages_from_reader(qp_pdf)

    # -----------------------------------------------
    # Add Qr code and Reg No string each page
    # -----------------------------------------------
    output_pdf = add_qr_code_to_pdf(output_pdf, reg_no, room, seat)
    output_path = os.path.join(f"{student_dir}/qp", f'{room}-{seat}-{reg_no}.pdf')
    with open(output_path, 'wb') as output_file:
        output_pdf.write(output_file)

    # ------------------------------------------------
    # Insert student details in the pdf
    # ------------------------------------------------
    details = [full_name, reg_no, f'{room}-{seat}']
    fill_student_details(output_path, fields, details)

    # -------------------------------------------------
    # Fill details in csv file to produce desk stickers
    # -------------------------------------------------
    full_name = ' '.join(full_name.split()).title() # Removing extra spaces if any

    return None

# df = df[ df['Taking midsem'] == 'yes' ]

Parallel(n_jobs=-1)( delayed(runner)(pair) for pair in tqdm(df.iterrows()) )

os.system(f"rm {student_dir}/qp.zip")
os.system(f"zip -r {student_dir}/qp.zip {student_dir}/qp")

print(f'{len(df)} question paers are saved in {student_dir}/qp')
