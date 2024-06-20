Very basic (heavily WIP) resume screener that I wrote up as a favour for a small business.

You should have a `resumes` folder in the script directory, as well as a `keywords.txt` file that contains comma separated keywords of interest. (e.g. `IT,businessman,headbusinessman`)

The script will scan each resume in the `resumes` folder and increment the total 'score' of the resume when it comes across a keyword.

A `resumelist` text file is then created that contains a list of the resumes and their respective score.

Supported file types:

- doc
- docx
- rtf
- txt
- pdf

Dependencies:

- docx2python
- pdfplumber
- re
- os
- pypandoc
- comtypes.client
