MAIN = exam # Name of the pdf file without the .pdf extension
PDF  = $(MAIN).pdf

qp:
	python3 ../generate-qp.py $(PDF)

read-scanned:
	python3 ../read-scanned-answerbooks.py	

.PHONY: qp read-scanned
