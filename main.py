from docx2python import docx2python
import pdfplumber
import re
import os
import pypandoc
import comtypes.client
import nltk
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import pandas as pd

def extract_text_docx(path):
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

descriptionFile = open('jobdescription.txt', 'r') 
descriptionString = descriptionFile.read()

cleanDescription = descriptionString.lower()
cleanDescription = re.sub(r'[^\w\s]', '', cleanDescription)
cleanDescription = cleanDescription.strip()
cleanDescription = re.sub('[0-9]+', '', cleanDescription)
cleanDescription = word_tokenize(cleanDescription)
stop = stopwords.words('english')
cleanDescription = [w for w in cleanDescription if not w in stop] 
cleanDescription = ' '.join(cleanDescription)

resumePaths = []
resumeStartPath = "resumes/"

resumes = os.listdir('resumes')
for resume in resumes:
    resumePaths.append(resumeStartPath + resume)

def calculate_resume_similarity(text):
    resume = CountVectorizer(stop_words='english')
    count_matrix = resume.fit_transform(text)

    similarityPercentage = cosine_similarity(count_matrix)[0][1] * 100
    similarityPercentage = round(similarityPercentage, 2)
    return similarityPercentage

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = text.strip()
    text = re.sub('[0-9]+', '', text)
    words = word_tokenize(text)
    stop_words = stopwords.words('english')
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

final_resume_data = {'Resume Name': [],
                    'Keyword Hits': [],
                    'Similarity Score': []
}

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
    resume_text = preprocess_text(resume_text)
    text = [resume_text, cleanDescription]
    similarity = calculate_resume_similarity(text)
    final_resume_data['Resume Name'].append(resumeFile)
    final_resume_data['Keyword Hits'].append(hits)
    final_resume_data['Similarity Score'].append(similarity)

resumeDataFrame = pd.DataFrame(final_resume_data)
resumeDataFrame.to_csv('ResumeData.csv', index=False)
