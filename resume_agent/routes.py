"""
Flask Routes for Resume Screener & Matcher Agent
Web interface for uploading resumes, job descriptions, and viewing results
"""

import os
import json
from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename

from .agent import ResumeScreenerAgent

# Create Blueprint
resume_bp = Blueprint('resume', __name__, url_prefix='/resume')

# Initialize agent
agent = ResumeScreenerAgent(storage_path='resume_data')

# Configuration
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@resume_bp.route('/')
def dashboard():
    """Resume screener dashboard"""
    stats = agent.get_statistics()
    return render_template('resume_dashboard.html', stats=stats)


@resume_bp.route('/upload', methods=['GET', 'POST'])
def upload_resume():
    """Upload single or multiple resumes"""
    message = ''
    error = ''
    uploaded_files = []
    
    if request.method == 'POST':
        try:
            # Check if multiple files or single file
            if 'resumes' in request.files:
                files = request.files.getlist('resumes')
            else:
                files = [request.files.get('resume')]
            
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    
                    # Process the resume
                    resume_info = agent.process_resume(filepath)
                    uploaded_files.append({
                        'filename': filename,
                        'email': resume_info.get('email', ''),
                        'skills': resume_info.get('skills', [])
                    })
            
            if uploaded_files:
                message = f'Successfully processed {len(uploaded_files)} resume(s)!'
            else:
                error = 'No valid files uploaded!'
                
        except Exception as e:
            error = f'Error processing files: {str(e)}'
    
    return render_template(
        'resume_upload.html',
        message=message,
        error=error,
        uploaded_files=uploaded_files
    )


@resume_bp.route('/screen', methods=['GET', 'POST'])
def screen_candidates():
    """Screen candidates against a job description"""
    results = []
    job_description = ''
    min_score = 0
    error = ''
    
    if request.method == 'POST':
        try:
            job_description = request.form.get('job_description', '')
            min_score = float(request.form.get('min_score', 0))
            
            if not job_description.strip():
                error = 'Please enter a job description!'
            else:
                results = agent.screen_candidates(
                    job_description=job_description,
                    min_score=min_score,
                    max_results=50
                )
                
        except Exception as e:
            error = f'Error screening candidates: {str(e)}'
    
    return render_template(
        'resume_screen.html',
        results=results,
        job_description=job_description,
        min_score=min_score,
        error=error
    )


@resume_bp.route('/match/<resume_id>', methods=['GET', 'POST'])
def match_resume(resume_id):
    """Match a specific resume to a job description"""
    resume = agent.get_resume(resume_id)
    if not resume:
        return redirect(url_for('resume.dashboard'))
    
    match_result = None
    job_description = ''
    error = ''
    
    if request.method == 'POST':
        try:
            job_description = request.form.get('job_description', '')
            
            if not job_description.strip():
                error = 'Please enter a job description!'
            else:
                match_result = agent.match_resume_to_job(resume_id, job_description)
                
        except Exception as e:
            error = f'Error matching resume: {str(e)}'
    
    return render_template(
        'resume_match.html',
        resume=resume,
        match_result=match_result,
        job_description=job_description,
        error=error
    )


@resume_bp.route('/api/upload', methods=['POST'])
def api_upload_resume():
    """API endpoint for uploading resumes"""
    try:
        if 'resumes' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('resumes')
        results = []
        
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                resume_info = agent.process_resume(filepath)
                results.append({
                    'id': resume_info.get('id'),
                    'email': resume_info.get('email'),
                    'skills': resume_info.get('skills', []),
                    'processed_at': resume_info.get('processed_at')
                })
        
        return jsonify({
            'success': True,
            'count': len(results),
            'resumes': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@resume_bp.route('/api/screen', methods=['POST'])
def api_screen_candidates():
    """API endpoint for screening candidates"""
    try:
        data = request.get_json()
        
        if not data or 'job_description' not in data:
            return jsonify({'error': 'Job description required'}), 400
        
        job_description = data.get('job_description')
        min_score = float(data.get('min_score', 0))
        max_results = int(data.get('max_results', 50))
        
        results = agent.screen_candidates(
            job_description=job_description,
            min_score=min_score,
            max_results=max_results
        )
        
        return jsonify({
            'success': True,
            'count': len(results),
            'candidates': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@resume_bp.route('/api/match', methods=['POST'])
def api_match_resume():
    """API endpoint for matching a resume to a job"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        resume_id = data.get('resume_id')
        job_description = data.get('job_description')
        
        if not resume_id or not job_description:
            return jsonify({'error': 'resume_id and job_description required'}), 400
        
        result = agent.match_resume_to_job(resume_id, job_description)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify({
            'success': True,
            'match': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@resume_bp.route('/api/resumes', methods=['GET'])
def api_get_resumes():
    """API endpoint to get all resumes"""
    resumes = agent.get_all_resumes()
    return jsonify({
        'success': True,
        'count': len(resumes),
        'resumes': resumes
    })


@resume_bp.route('/api/stats', methods=['GET'])
def api_get_stats():
    """API endpoint to get statistics"""
    stats = agent.get_statistics()
    return jsonify({
        'success': True,
        'stats': stats
    })


@resume_bp.route('/export', methods=['POST'])
def export_results():
    """Export screening results to file"""
    try:
        job_description = request.form.get('job_description', '')
        format_type = request.form.get('format', 'json')
        
        if not job_description:
            return redirect(url_for('resume.screen_candidates'))
        
        timestamp = os.path.basename(os.path.splitext(job_description)[0])[:20]
        output_filename = f'results_{timestamp}.{format_type}'
        output_path = os.path.join('static', output_filename)
        
        agent.export_results(job_description, output_path, format_type)
        
        return send_file(output_path, as_attachment=True)
        
    except Exception as e:
        return f'Error exporting results: {str(e)}', 500


@resume_bp.route('/delete/<resume_id>', methods=['POST'])
def delete_resume(resume_id):
    """Delete a resume from the database"""
    try:
        success = agent.delete_resume(resume_id)
        if success:
            return jsonify({'success': True, 'message': 'Resume deleted'})
        else:
            return jsonify({'error': 'Resume not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@resume_bp.route('/clear', methods=['POST'])
def clear_database():
    """Clear all resumes from database"""
    try:
        agent.clear_database()
        return redirect(url_for('resume.dashboard'))
    except Exception as e:
        return f'Error clearing database: {str(e)}', 500
