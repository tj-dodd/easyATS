from flask import Flask, request, render_template, redirect, url_for
import os
import re
import pdfplumber
import pypandoc
from docx2python import docx2python
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

UPLOAD_FOLDER = '/uploads'

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

def extract_text_from_rtf(file_path):
    return pypandoc.convert_file(file_path, 'plain')

def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def screen_resume(resume_text, keywordsString):
    hits = sum(1 for keyword in keywordsString if re.search(r'\b' + re.escape(keyword) + r'\b', resume_text, re.IGNORECASE))
    return hits

def calculate_resume_similarity(text):
    resume = CountVectorizer(stop_words='english')
    count_matrix = resume.fit_transform(text)
    similarityPercentage = cosine_similarity(count_matrix)[0][1] * 100
    similarityPercentage = round(similarityPercentage + 1, 2)
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if request.method == 'POST':
        # Save uploaded files
        job_description = request.files['jobdescription']
        resumes = request.files.getlist('resumes')
        keywords = request.files['keywords']

        keywords.filename = 'keywords.txt'
        job_description.filename = 'jobdescription.txt'
        
        keywords.save(os.path.join('uploads', keywords.filename))
        job_description.save(os.path.join('uploads', job_description.filename))
        for resume in resumes:
            resume.save(os.path.join('uploads', resume.filename))
        return redirect(url_for('process_files'))

@app.route('/delete_files')
def delete_files():
    upload_folder = 'uploads'
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    return redirect(url_for('index'))

@app.route('/process')
def process_files():
    # Read keywords and job description
    with open('uploads/keywords.txt', 'r', encoding='utf-8') as keywordFile:
        keywordsString = keywordFile.read().split(',')
    
    with open('uploads/jobdescription.txt', 'r') as descriptionFile:
        descriptionString = descriptionFile.read()
        
    stop = stopwords.words('english')
    cleanDescription = descriptionString.lower()
    cleanDescription = re.sub(r'[^\w\s]', '', cleanDescription)
    cleanDescription = cleanDescription.strip()
    cleanDescription = re.sub('[0-9]+', '', cleanDescription)
    cleanDescription = word_tokenize(cleanDescription)
    cleanDescription = [w for w in cleanDescription if not w in stop] 
    cleanDescription = ' '.join(cleanDescription)

    resumePaths = []
    resumeStartPath = "uploads/"

    resumes = os.listdir('uploads')
    for resume in resumes:
        if ((resume != 'jobdescription.txt') and (resume != 'keywords.txt')):
            resumePaths.append(resumeStartPath + resume)

    final_resume_data = {'Resume Name': [], 'Keyword Hits': [], 'Similarity Score': []}
    
    for resumeFile in resumePaths:
        file_extension = resumeFile.split('.')[-1].lower()
        if file_extension == 'docx':
            resume_text = extract_text_docx(resumeFile)
        elif file_extension == 'pdf':
            resume_text = extract_text_pdf(resumeFile)
        elif file_extension == 'doc':
            resume_text = extract_text_docx(resumeFile)
        elif file_extension == 'rtf':
            resume_text = extract_text_from_rtf(resumeFile)
        elif file_extension == 'txt':
            resume_text = extract_text_from_txt(resumeFile)
        else:
            continue

        resume_text = preprocess_text(resume_text)
        text = [resume_text, cleanDescription]

        hits = screen_resume(resume_text, keywordsString)
        similarity = calculate_resume_similarity(text)

        final_resume_data['Resume Name'].append(resumeFile.removeprefix("uploads/"))
        final_resume_data['Keyword Hits'].append(hits)
        final_resume_data['Similarity Score'].append(similarity)

    resumeDataFrame = pd.DataFrame(final_resume_data)
    resumeDataFrame.to_csv('static/ResumeData.csv', index=False)
    return render_template('results.html', resume_data=resumeDataFrame.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=False)
