"""
Resume Parser Module
Handles parsing of resumes in PDF, DOCX, and TXT formats
"""

import os
import re
from typing import Dict, List, Optional


class ResumeParser:
    """Parse resumes from various formats and extract structured information"""
    
    def __init__(self):
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}'
        
    def parse_file(self, file_path: str) -> Dict:
        """
        Parse a resume file and extract information
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dictionary containing extracted resume information
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            text = self._parse_pdf(file_path)
        elif ext == '.docx':
            text = self._parse_docx(file_path)
        elif ext == '.txt':
            text = self._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        return self._extract_info(text)
    
    def _parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except ImportError:
            raise ImportError("Please install pdfplumber: pip install pdfplumber")
    
    def _parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except ImportError:
            raise ImportError("Please install python-docx: pip install python-docx")
    
    def _parse_txt(self, file_path: str) -> str:
        """Read text from TXT file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _extract_info(self, text: str) -> Dict:
        """
        Extract structured information from resume text
        
        Args:
            text: Raw resume text
            
        Returns:
            Dictionary with extracted fields
        """
        info = {
            'raw_text': text,
            'email': '',
            'phone': '',
            'name': '',
            'skills': [],
            'experience': [],
            'education': [],
            'certifications': []
        }
        
        # Extract email
        emails = re.findall(self.email_pattern, text)
        if emails:
            info['email'] = emails[0]
        
        # Extract phone
        phones = re.findall(self.phone_pattern, text)
        if phones:
            info['phone'] = phones[0]
        
        # Extract skills (common tech skills)
        info['skills'] = self._extract_skills(text)
        
        # Extract experience
        info['experience'] = self._extract_experience(text)
        
        # Extract education
        info['education'] = self._extract_education(text)
        
        # Extract certifications
        info['certifications'] = self._extract_certifications(text)
        
        return info
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        # Common technical skills to look for
        skill_keywords = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
            'React', 'Angular', 'Vue', 'Django', 'Flask', 'FastAPI', 'Spring Boot',
            'Node.js', 'Express', 'Next.js', 'Nuxt.js',
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform',
            'Git', 'CI/CD', 'Jenkins', 'GitHub Actions', 'GitLab CI',
            'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Scikit-learn',
            'Data Analysis', 'Pandas', 'NumPy', 'Matplotlib', 'Tableau',
            'Agile', 'Scrum', 'Kanban', 'REST API', 'GraphQL', 'Microservices',
            'HTML', 'CSS', 'SASS', 'Tailwind', 'Bootstrap',
            'Linux', 'Bash', 'PowerShell', 'DevOps', 'Cloud Computing'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience from resume"""
        experiences = []
        
        # Look for patterns like "Company Name - Position (Year-Year)"
        pattern = r'([A-Za-z\s]+)\s*[-–]\s*([A-Za-z\s]+)\s*\((\d{4})\s*[-–]?\s*(\d{4}|Present|present)\)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            experiences.append({
                'company': match.group(1).strip(),
                'position': match.group(2).strip(),
                'start_year': match.group(3),
                'end_year': match.group(4)
            })
        
        # If no structured format found, look for company/role mentions
        if not experiences:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['engineer', 'developer', 'manager', 'director', 'lead', 'senior', 'junior']):
                    experiences.append({
                        'description': line.strip(),
                        'context': lines[i-1:i+2] if i > 0 else [line]
                    })
        
        return experiences[:5]  # Limit to 5 most relevant
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information from resume"""
        educations = []
        
        # Look for degree patterns
        degree_keywords = ['Bachelor', 'Master', 'PhD', 'B.S', 'M.S', 'B.Tech', 'M.Tech', 
                          'B.E', 'M.E', 'MBA', 'BBA', 'Associate']
        
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line for keyword in degree_keywords):
                educations.append({
                    'degree': line.strip(),
                    'institution': self._extract_institution(line)
                })
        
        return educations[:3]  # Limit to 3 most recent
    
    def _extract_institution(self, text: str) -> str:
        """Extract institution name from education line"""
        # Simple heuristic: look for university/college/institute keywords
        keywords = ['University', 'College', 'Institute', 'School', 'Academy']
        words = text.split()
        
        for i, word in enumerate(words):
            if any(kw in word for kw in keywords):
                return ' '.join(words[max(0, i-2):min(len(words), i+3)])
        
        return ''
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from resume"""
        cert_keywords = [
            'AWS Certified', 'Azure Certified', 'Google Cloud Certified',
            'PMP', 'Certified Scrum Master', 'CSM', 'Six Sigma',
            'Cisco Certified', 'CCNA', 'CCNP', 'CompTIA',
            'Oracle Certified', 'Microsoft Certified', 'Salesforce Certified'
        ]
        
        found_certs = []
        for cert in cert_keywords:
            if cert.lower() in text.lower():
                found_certs.append(cert)
        
        return found_certs
