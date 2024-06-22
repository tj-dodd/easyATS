# Easy Resume Screener

Basic resume screener that I wrote up as a favour for a small business.

The app will ask for a list of resumes as well as a keywords file and job description file (both of these should be in .txt format). The app will scan each provided resume (supported file types listed below) and increment the total 'score' of a resume when it comes across a keyword. It will also generate a similarity score (job description as reference) using cosine similarity. The similarity score gives you a rough idea of candidate suitability, however it is heavily deflated.

Results are then provided in a sortable table.

Supported file types:

- doc
- docx
- rtf
- txt
- pdf

Dependencies:

- docx2python
- pdfplumber
- pypandoc
- nltk
- pandas
- sklearn
- flask

Install all packages with `pip install -r requirements.txt`.
