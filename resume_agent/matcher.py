"""
Resume Matcher Module
Matches resumes against job descriptions using ML-based scoring
"""

import numpy as np
from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ResumeMatcher:
    """Match resumes against job descriptions and rank candidates"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
    
    def calculate_match_score(self, resume_info: Dict, job_description: str) -> float:
        """
        Calculate match score between a resume and job description
        
        Args:
            resume_info: Parsed resume information dictionary
            job_description: Job description text
            
        Returns:
            Match score between 0 and 100
        """
        # Combine all resume text for comparison
        resume_text = resume_info.get('raw_text', '')
        
        if not resume_text.strip() or not job_description.strip():
            return 0.0
        
        try:
            # Create TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform([resume_text, job_description])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Boost score based on skills match
            skills_boost = self._calculate_skills_match(
                resume_info.get('skills', []),
                job_description
            )
            
            # Final score (70% similarity + 30% skills match)
            final_score = (similarity * 0.7 + skills_boost * 0.3) * 100
            
            return round(final_score, 2)
            
        except Exception as e:
            print(f"Error calculating match score: {e}")
            return 0.0
    
    def _calculate_skills_match(self, resume_skills: List[str], job_description: str) -> float:
        """
        Calculate skills match percentage
        
        Args:
            resume_skills: List of skills from resume
            job_description: Job description text
            
        Returns:
            Skills match score between 0 and 1
        """
        if not resume_skills:
            return 0.0
        
        # Common required skills keywords in job descriptions
        required_skill_patterns = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular',
            'node.js', 'django', 'flask', 'sql', 'mongodb', 'aws', 'azure',
            'docker', 'kubernetes', 'machine learning', 'deep learning',
            'rest api', 'graphql', 'microservices', 'ci/cd', 'git'
        ]
        
        # Extract required skills from job description
        job_desc_lower = job_description.lower()
        required_skills = [
            skill for skill in required_skill_patterns
            if skill in job_desc_lower
        ]
        
        if not required_skills:
            # If no specific skills found in JD, use general similarity
            return 0.5
        
        # Count matching skills
        resume_skills_lower = [s.lower() for s in resume_skills]
        matched_skills = sum(
            1 for skill in required_skills
            if any(skill in resume_skill.lower() for resume_skill in resume_skills)
        )
        
        return matched_skills / len(required_skills)
    
    def rank_candidates(self, resumes: List[Dict], job_description: str) -> List[Tuple[int, float, Dict]]:
        """
        Rank multiple candidates based on match score
        
        Args:
            resumes: List of parsed resume dictionaries with 'id' field
            job_description: Job description text
            
        Returns:
            List of tuples (resume_id, match_score, resume_info) sorted by score descending
        """
        scored_resumes = []
        
        for resume in resumes:
            resume_id = resume.get('id', resume.get('email', 'unknown'))
            score = self.calculate_match_score(resume, job_description)
            scored_resumes.append((resume_id, score, resume))
        
        # Sort by score descending
        scored_resumes.sort(key=lambda x: x[1], reverse=True)
        
        return scored_resumes
    
    def get_top_candidates(self, resumes: List[Dict], job_description: str, top_n: int = 10) -> List[Dict]:
        """
        Get top N candidates for a job
        
        Args:
            resumes: List of parsed resume dictionaries
            job_description: Job description text
            top_n: Number of top candidates to return
            
        Returns:
            List of top candidate dictionaries with scores
        """
        ranked = self.rank_candidates(resumes, job_description)
        
        top_candidates = []
        for resume_id, score, resume_info in ranked[:top_n]:
            candidate = resume_info.copy()
            candidate['match_score'] = score
            candidate['rank'] = len(top_candidates) + 1
            top_candidates.append(candidate)
        
        return top_candidates
    
    def analyze_skill_gaps(self, resume_info: Dict, job_description: str) -> Dict:
        """
        Analyze skill gaps between resume and job requirements
        
        Args:
            resume_info: Parsed resume information
            job_description: Job description text
            
        Returns:
            Dictionary containing skill analysis
        """
        resume_skills = set(s.lower() for s in resume_info.get('skills', []))
        
        # Extract skills from job description
        common_skills = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'fastapi', 'spring boot',
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch',
            'rest api', 'graphql', 'microservices', 'ci/cd', 'git',
            'agile', 'scrum', 'devops'
        ]
        
        job_desc_lower = job_description.lower()
        required_skills = set(
            skill for skill in common_skills
            if skill in job_desc_lower
        )
        
        matched_skills = resume_skills.intersection(required_skills)
        missing_skills = required_skills - resume_skills
        
        return {
            'matched_skills': list(matched_skills),
            'missing_skills': list(missing_skills),
            'total_required': len(required_skills),
            'total_matched': len(matched_skills),
            'coverage_percentage': round(len(matched_skills) / len(required_skills) * 100, 2) if required_skills else 0
        }
