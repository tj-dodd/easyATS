from docx2python import docx2python
import pdfplumber
import re
import os
import pypandoc
import comtypes.client

def extract_text_docx(path):
    document_text = []
    with docx2python(path) as docx_content:
        document_text = docx_content.text
    return document_text

def extract_text_pdf(path):
    text = ''
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def convert_doc_docx(path):
    word = comtypes.client.CreateObject('Word.Application')
    abs = os.path.abspath(path)
    doc = word.Documents.Open(abs)
    docx_path = os.path.splitext(abs)[0] + '.docx'
    doc.SaveAs(docx_path, FileFormat=16)
    doc.Close()
    word.Quit()
    return docx_path

def extract_text_from_doc(path):
    docx_path = convert_doc_docx(path)
    return extract_text_docx(docx_path)

def extract_text_from_rtf(file_path):
    return pypandoc.convert_file(file_path, 'plain')

def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def screen_resume(resume_text, keywordsString):
    hits = sum(1 for keyword in keywordsString if re.search(r'\b' + re.escape(keyword) + r'\b', resume_text, re.IGNORECASE))
    return hits

keywordFile = open('keywords.txt', 'r', encoding='utf-8')
keywordsString = keywordFile.read().split(',')

resumePaths = []
resumeStartPath = "resumes/"

totalResumes = 0

resumes = os.listdir('resumes')
for resume in resumes:
    resumePaths.append(resumeStartPath + resume)
    totalResumes += 1

resumeList = open("resumelist.txt", "w").close()
selected_resumes = []
for resumeFile in resumePaths:
    file_extension = resumeFile.split('.')[-1].lower()
    if file_extension == 'docx':
        resume_text = extract_text_docx(resumeFile)
    elif file_extension == 'pdf':
        resume_text = extract_text_pdf(resumeFile)
    elif file_extension == 'doc':
        resume_text = extract_text_from_doc(resumeFile)
    elif file_extension == 'rtf':
        resume_text = extract_text_from_rtf(resumeFile)
    elif file_extension == 'txt':
        resume_text = extract_text_from_txt(resumeFile)
    else:
        print(f"Unsupported file type: {resumeFile}")
        continue
    hits = screen_resume(resume_text, keywordsString)
    resumeRanking = resumeFile + ": " + str(hits) + "\n"
    newResumeList = open("resumelist.txt", "a")
    newResumeList.write(resumeRanking)
