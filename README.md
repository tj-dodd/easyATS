# Easy Resume Screener

Basic resume screener that I wrote up as a favour for a small business.

You should have a `resumes` folder in the home directory, as well as a `keywords.txt` file that contains comma separated keywords of interest. (e.g. `IT,businessman,headbusinessman`). The description for the job should be present in the home directory under `jobdescription.txt`.

The script will scan each resume in the `resumes` folder and increment the total 'score' of the resume when it comes across a keyword. It will also generate a similarity score (job description as reference) using cosine similarity. The similarity score gives you a rough idea of candidate suitability, however it is heavily deflated.

A `ResumeData.csv` file is then created that contains all resumes and their respective scores/similarities.

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
- comtypes.client
- nltk
- pandas
- sklearn

Install packages with `pip install -r requirements.txt`
