import os
from flask import Flask, request, render_template, redirect, url_for, flash, session
import re
import pdfplumber
import pypandoc
from docx2python import docx2python
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resumes.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'defaultsecretkey')

db = SQLAlchemy(app)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    path = db.Column(db.String(300), nullable=False)
    session_id = db.Column(db.String(200), nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'rtf', 'txt', 'doc'}

def extract_text(file_path):
    file_extension = file_path.split('.')[-1].lower()
    if file_extension == 'docx':
        return extract_text_docx(file_path)
    elif file_extension == 'doc':
        return extract_text_docx(file_path)
    elif file_extension == 'pdf':
        return extract_text_pdf(file_path)
    elif file_extension == 'rtf':
        return extract_text_from_rtf(file_path)
    elif file_extension == 'txt':
        return extract_text_from_txt(file_path)
    else:
        return None

def extract_text_docx(path):
    with docx2python(path) as docx_content:
        return docx_content.text

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

def screen_resume(resume_text, keywords):
    hits = sum(1 for keyword in keywords if re.search(r'\b' + re.escape(keyword) + r'\b', resume_text, re.IGNORECASE))
    return hits

def calculate_resume_similarity(texts):
    resume = CountVectorizer(stop_words='english')
    count_matrix = resume.fit_transform(texts)
    similarity_percentage = cosine_similarity(count_matrix)[0][1] * 100
    return round(similarity_percentage + 1, 2)

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text is text.strip()
    text = re.sub('[0-9]+', '', text)
    words = word_tokenize(text)
    stop_words = stopwords.words('english')
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

@app.before_request
def session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST', 'GET'])
def upload_files():
    job_description = request.files['jobdescription']
    keywords = request.files['keywords']
    resumes = request.files.getlist('resumes')

    keywords.filename = 'keywords.txt'
    job_description.filename = 'jobdescription.txt'

    if not job_description or not allowed_file(job_description.filename):
        flash('Invalid job description file')
        return redirect(request.url)
    
    if not keywords or not allowed_file(keywords.filename):
        flash('Invalid keywords file')
        return redirect(request.url)

    if not all(allowed_file(resume.filename) for resume in resumes):
        flash('Invalid resume files')
        return redirect(request.url)

    job_description_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(job_description.filename))
    keywords_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(keywords.filename))
    
    job_description.save(job_description_path)
    keywords.save(keywords_path)

    for resume in resumes:
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(resume.filename))
        resume.save(resume_path)
        
        new_resume = Resume(name=resume.filename, path=resume_path, session_id=session['session_id'])
        db.session.add(new_resume)
    
    db.session.commit()
    return redirect(url_for('process_files'))

@app.route('/delete_files')
def delete_files():
    resumes = Resume.query.filter_by(session_id=session['session_id']).all()
    for resume in resumes:
        if os.path.isfile(resume.path):
            os.remove(resume.path)
        db.session.delete(resume)
    
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/process', methods=['GET'])
def process_files():
    keywords_path = os.path.join(app.config['UPLOAD_FOLDER'], 'keywords.txt')
    job_description_path = os.path.join(app.config['UPLOAD_FOLDER'], 'jobdescription.txt')
    
    with open(keywords_path, 'r', encoding='utf-8') as keyword_file:
        keywords = keyword_file.read().split(',')

    with open(job_description_path, 'r', encoding='utf-8') as description_file:
        description = preprocess_text(description_file.read())

    resumes = Resume.query.filter_by(session_id=session['session_id']).all()
    final_resume_data = {'Resume Name': [], 'Keyword Hits': [], 'Similarity Score': []}

    for resume in resumes:
        resume_text = extract_text(resume.path)
        if resume_text:
            resume_text = preprocess_text(resume_text)
            texts = [resume_text, description]
            hits = screen_resume(resume_text, keywords)
            similarity = calculate_resume_similarity(texts)

            final_resume_data['Resume Name'].append(resume.name)
            final_resume_data['Keyword Hits'].append(hits)
            final_resume_data['Similarity Score'].append(similarity)

    resume_df = pd.DataFrame(final_resume_data)
    resume_df.to_csv(os.path.join('static', 'ResumeData.csv'), index=False)
    return render_template('results.html', resume_data=resume_df.to_dict(orient='records'))

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)
