# Resume Screener & Matcher Agent

An AI-powered resume screening and matching system that parses thousands of resumes instantly and matches them against job descriptions using machine learning.

## Features

- **Multi-format Support**: Parse resumes in PDF, DOCX, and TXT formats
- **Intelligent Parsing**: Extract skills, experience, education, and certifications
- **ML-based Matching**: TF-IDF vectorization with cosine similarity for accurate matching
- **Skill Gap Analysis**: Identify missing skills between candidate and job requirements
- **Batch Processing**: Process thousands of resumes efficiently
- **REST API**: Full API support for integration with other systems
- **Web Interface**: Modern, responsive UI for easy use
- **Export Results**: Download screening results as JSON or CSV

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <project-directory>
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5003`

### Production Deployment (Heroku)

1. Install Heroku CLI and login:
```bash
heroku login
```

2. Create a new Heroku app:
```bash
heroku create your-app-name
```

3. Deploy:
```bash
git add .
git commit -m "Initial deployment"
git push heroku main
```

4. Open your app:
```bash
heroku open
```

## Usage

### Web Interface

1. **Upload Resumes**: Navigate to `/resume/upload` and upload PDF, DOCX, or TXT files
2. **Screen Candidates**: Go to `/resume/screen`, paste a job description, and get ranked results
3. **Match Individual**: Click on any candidate to see detailed match analysis

### API Endpoints

#### Upload Resumes
```bash
POST /resume/api/upload
Content-Type: multipart/form-data

Files: resumes[] (multiple files)
```

#### Screen Candidates
```bash
POST /resume/api/screen
Content-Type: application/json

{
    "job_description": "Your job description here...",
    "min_score": 50,
    "max_results": 50
}
```

#### Match Single Resume
```bash
POST /resume/api/match
Content-Type: application/json

{
    "resume_id": "candidate@email.com",
    "job_description": "Your job description here..."
}
```

#### Get All Resumes
```bash
GET /resume/api/resumes
```

#### Get Statistics
```bash
GET /resume/api/stats
```

## Project Structure

```
/workspace
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Heroku deployment config
├── resume_agent/         # Resume screener package
│   ├── __init__.py
│   ├── parser.py         # Resume parsing module
│   ├── matcher.py        # ML-based matching module
│   ├── agent.py          # Main agent orchestration
│   └── routes.py         # Flask routes and API
├── templates/            # HTML templates
│   ├── resume_dashboard.html
│   ├── resume_upload.html
│   ├── resume_screen.html
│   └── resume_match.html
├── uploads/              # Uploaded files storage
├── resume_data/          # Processed resume database
└── static/               # Generated output files
```

## Technology Stack

- **Backend**: Flask (Python 3.10+)
- **ML/NLP**: scikit-learn, NLTK
- **Document Parsing**: pdfplumber, python-docx
- **Data Processing**: pandas, numpy
- **Deployment**: Gunicorn, Heroku-ready

## Configuration

### Environment Variables

- `PORT`: Server port (default: 5003 for local, dynamic for Heroku)
- `SECRET_KEY`: Flask secret key for sessions

### File Upload Limits

Modify `MAX_CONTENT_LENGTH` in `app.py` to change upload size limits.

## License

MIT License - Feel free to use and modify for your needs!

## Support

For issues and feature requests, please open an issue on GitHub.
