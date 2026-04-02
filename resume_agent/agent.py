"""
Resume Screener & Matcher Agent
Main agent class that orchestrates parsing, matching, and screening
"""

import os
import json
from typing import Dict, List, Optional, Union
from datetime import datetime

from .parser import ResumeParser
from .matcher import ResumeMatcher


class ResumeScreenerAgent:
    """
    Main agent for screening and matching resumes against job descriptions
    
    Features:
    - Parse resumes in PDF, DOCX, TXT formats
    - Extract skills, experience, education, certifications
    - Match resumes against job descriptions using ML
    - Rank candidates by fit score
    - Analyze skill gaps
    - Batch processing for thousands of resumes
    """
    
    def __init__(self, storage_path: str = 'resume_data'):
        """
        Initialize the Resume Screener Agent
        
        Args:
            storage_path: Path to store processed resume data
        """
        self.parser = ResumeParser()
        self.matcher = ResumeMatcher()
        self.storage_path = storage_path
        self.resumes_db = {}  # In-memory database for demo; use DB in production
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing resume database if available
        self._load_database()
    
    def _load_database(self):
        """Load resume database from disk"""
        db_path = os.path.join(self.storage_path, 'resumes_db.json')
        if os.path.exists(db_path):
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    self.resumes_db = json.load(f)
            except Exception as e:
                print(f"Error loading database: {e}")
                self.resumes_db = {}
    
    def _save_database(self):
        """Save resume database to disk"""
        db_path = os.path.join(self.storage_path, 'resumes_db.json')
        try:
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(self.resumes_db, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def process_resume(self, file_path: str, resume_id: Optional[str] = None) -> Dict:
        """
        Process a single resume file
        
        Args:
            file_path: Path to the resume file
            resume_id: Optional custom ID for the resume
            
        Returns:
            Dictionary containing parsed resume information
        """
        # Parse the resume
        resume_info = self.parser.parse_file(file_path)
        
        # Generate ID if not provided
        if not resume_id:
            resume_id = resume_info.get('email', f"resume_{len(self.resumes_db) + 1}")
        
        # Add metadata
        resume_info['id'] = resume_id
        resume_info['processed_at'] = datetime.now().isoformat()
        resume_info['file_path'] = file_path
        
        # Store in database
        self.resumes_db[resume_id] = resume_info
        self._save_database()
        
        return resume_info
    
    def process_multiple_resumes(self, file_paths: List[str]) -> List[Dict]:
        """
        Process multiple resume files in batch
        
        Args:
            file_paths: List of paths to resume files
            
        Returns:
            List of processed resume dictionaries
        """
        results = []
        total = len(file_paths)
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                print(f"Processing resume {i}/{total}: {file_path}")
                resume_info = self.process_resume(file_path)
                results.append(resume_info)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                results.append({
                    'file_path': file_path,
                    'error': str(e),
                    'processed_at': datetime.now().isoformat()
                })
        
        return results
    
    def screen_candidates(
        self,
        job_description: str,
        min_score: float = 0.0,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Screen all resumes in database against a job description
        
        Args:
            job_description: Job description text
            min_score: Minimum match score threshold (0-100)
            max_results: Maximum number of results to return
            
        Returns:
            List of candidate dictionaries sorted by match score
        """
        if not self.resumes_db:
            return []
        
        resumes_list = list(self.resumes_db.values())
        
        # Get top candidates
        top_candidates = self.matcher.get_top_candidates(
            resumes_list,
            job_description,
            top_n=max_results
        )
        
        # Filter by minimum score
        filtered_candidates = [
            candidate for candidate in top_candidates
            if candidate.get('match_score', 0) >= min_score
        ]
        
        return filtered_candidates
    
    def match_resume_to_job(self, resume_id: str, job_description: str) -> Dict:
        """
        Match a specific resume to a job description
        
        Args:
            resume_id: ID of the resume to match
            job_description: Job description text
            
        Returns:
            Dictionary containing match analysis
        """
        if resume_id not in self.resumes_db:
            return {'error': f'Resume {resume_id} not found'}
        
        resume_info = self.resumes_db[resume_id]
        
        # Calculate match score
        match_score = self.matcher.calculate_match_score(resume_info, job_description)
        
        # Analyze skill gaps
        skill_analysis = self.matcher.analyze_skill_gaps(resume_info, job_description)
        
        return {
            'resume_id': resume_id,
            'match_score': match_score,
            'skill_analysis': skill_analysis,
            'candidate_info': {
                'email': resume_info.get('email', ''),
                'skills': resume_info.get('skills', []),
                'experience': resume_info.get('experience', []),
                'education': resume_info.get('education', [])
            }
        }
    
    def get_resume(self, resume_id: str) -> Optional[Dict]:
        """Get a specific resume from the database"""
        return self.resumes_db.get(resume_id)
    
    def get_all_resumes(self) -> List[Dict]:
        """Get all resumes from the database"""
        return list(self.resumes_db.values())
    
    def delete_resume(self, resume_id: str) -> bool:
        """Delete a resume from the database"""
        if resume_id in self.resumes_db:
            del self.resumes_db[resume_id]
            self._save_database()
            return True
        return False
    
    def clear_database(self):
        """Clear all resumes from the database"""
        self.resumes_db = {}
        self._save_database()
    
    def get_statistics(self) -> Dict:
        """Get statistics about the resume database"""
        total_resumes = len(self.resumes_db)
        
        # Count skills frequency
        skills_count = {}
        for resume in self.resumes_db.values():
            for skill in resume.get('skills', []):
                skills_count[skill] = skills_count.get(skill, 0) + 1
        
        # Top skills
        top_skills = sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_resumes': total_resumes,
            'top_skills': [{'skill': skill, 'count': count} for skill, count in top_skills],
            'last_updated': datetime.now().isoformat()
        }
    
    def export_results(self, job_description: str, output_path: str, format: str = 'json') -> str:
        """
        Export screening results to a file
        
        Args:
            job_description: Job description used for screening
            output_path: Path to save the results
            format: Output format ('json' or 'csv')
            
        Returns:
            Path to the exported file
        """
        candidates = self.screen_candidates(job_description)
        
        if format.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'job_description': job_description,
                    'total_candidates': len(candidates),
                    'exported_at': datetime.now().isoformat(),
                    'candidates': candidates
                }, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == 'csv':
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Rank', 'Email', 'Match Score', 'Skills', 'Experience'])
                for candidate in candidates:
                    writer.writerow([
                        candidate.get('rank', ''),
                        candidate.get('email', ''),
                        candidate.get('match_score', ''),
                        ', '.join(candidate.get('skills', [])),
                        len(candidate.get('experience', []))
                    ])
        
        return output_path
