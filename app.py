from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os
import secrets

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = None
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shinwari.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'

# ============================================================
# LIMITS
# ============================================================
LIMITS = {
    'free': {
        'tts': 2000,
        'pdf_to_text': 20,
        'text_to_pdf': 20,
        'qr': 15,
        'translator': 1000,
        'image': 15,
        'word_to_pdf': 30,
        'pdf_to_word': 20,
        'image_to_text': 15,
    },
    'basic': {
        'tts': 10000,
        'pdf_to_text': 100,
        'text_to_pdf': 100,
        'qr': 100,
        'translator': 5000,
        'image': 100,
        'word_to_pdf': 100,
        'pdf_to_word': 100,
        'image_to_text': 100,
    },
    'pro': {
        'tts': 999999,
        'pdf_to_text': 999999,
        'text_to_pdf': 999999,
        'qr': 999999,
        'translator': 999999,
        'image': 999999,
        'word_to_pdf': 999999,
        'pdf_to_word': 999999,
        'image_to_text': 999999,
    }
}

# ============================================================
# DATABASE MODELS
# ============================================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    plan = db.Column(db.String(20), default='free')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usages = db.relationship('Usage', backref='user', lazy=True)

class Usage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tool = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0)
    reset_date = db.Column(db.Date, default=date.today)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_usage(tool):
    if not current_user.is_authenticated:
        return 0, LIMITS['free'][tool]
    today = date.today()
    usage = Usage.query.filter_by(
        user_id=current_user.id, tool=tool
    ).first()
    if not usage:
        usage = Usage(user_id=current_user.id, tool=tool, count=0)
        db.session.add(usage)
        db.session.commit()
    # Reset daily usage
    if usage.reset_date != today:
        usage.count = 0
        usage.reset_date = today
        db.session.commit()
    limit = LIMITS[current_user.plan][tool]
    return usage.count, limit

def increment_usage(tool, amount=1):
    if not current_user.is_authenticated:
        return
    today = date.today()
    usage = Usage.query.filter_by(
        user_id=current_user.id, tool=tool
    ).first()
    if not usage:
        usage = Usage(user_id=current_user.id, tool=tool, count=0)
        db.session.add(usage)
    if usage.reset_date != today:
        usage.count = 0
        usage.reset_date = today
    usage.count += amount
    db.session.commit()

def check_limit(tool, amount=1):
    if not current_user.is_authenticated:
        # Guest users get very limited access
        return True
    used, limit = get_usage(tool)
    return (used + amount) <= limit

# ============================================================
# AUTH ROUTES
# ============================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    error = ''
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        if not name or not email or not password:
            error = 'All fields are required!'
        elif password != confirm:
            error = 'Passwords do not match!'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered!'
        else:
            hashed = generate_password_hash(password)
            user = User(name=name, email=email, password=hashed)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    error = ''
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            error = 'Invalid email or password!'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    tools = [
        'tts', 'pdf_to_text', 'text_to_pdf', 'qr',
        'translator', 'image', 'word_to_pdf',
        'pdf_to_word', 'image_to_text'
    ]
    usage_data = {}
    for tool in tools:
        used, limit = get_usage(tool)
        usage_data[tool] = {
            'used': used,
            'limit': limit,
            'percent': min(int((used / limit) * 100), 100)
        }
    return render_template(
        'dashboard.html',
        usage_data=usage_data,
        plan=current_user.plan
    )

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# ============================================================
# HOME
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')

# ============================================================
# URDU TTS
# ============================================================
@app.route('/urdu-tts', methods=['GET', 'POST'])
def urdu_tts():
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            from gtts import gTTS
            import re
            text = ''
            txt_file = request.files.get('txt_file')
            if txt_file and txt_file.filename != '':
                text = txt_file.read().decode('utf-8', errors='replace')
            if not text:
                text = request.form.get('text', '')
            lang = request.form.get('lang', 'ur')
            if text.strip():
                word_count = len(text.split())
                if not check_limit('tts', word_count):
                    used, limit = get_usage('tts')
                    error = f'Daily limit reached! Used {used}/{limit} words. Upgrade to Pro for more.'
                else:
                    text = re.sub(r'[*#@&^%$~`<>|\\]', '', text)
                    text = re.sub(r'\s+', ' ', text)
                    tts = gTTS(text=text, lang=lang)
                    tts.save(os.path.join(STATIC_FOLDER, 'output.mp3'))
                    increment_usage('tts', word_count)
                    message = 'success'
            else:
                error = 'Text is empty!'
        except Exception as e:
            error = str(e)
    used, limit = get_usage('tts') if current_user.is_authenticated else (0, LIMITS['free']['tts'])
    return render_template('urdu_tts.html', message=message, error=error, used=used, limit=limit)

# ============================================================
# PDF TO TEXT
# ============================================================
@app.route('/pdf-to-text', methods=['GET', 'POST'])
def pdf_to_text():
    text = ''
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            import fitz
            if not check_limit('pdf_to_text'):
                used, limit = get_usage('pdf_to_text')
                error = f'Daily limit reached! Used {used}/{limit} files. Upgrade to Pro for more.'
            else:
                file = request.files.get('pdf_file')
                if file and file.filename.endswith('.pdf'):
                    path = os.path.join(UPLOAD_FOLDER, file.filename)
                    file.save(path)
                    doc = fitz.open(path)
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                    txt_path = os.path.join(STATIC_FOLDER, 'extracted.txt')
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    increment_usage('pdf_to_text')
                    message = 'success'
                else:
                    error = 'Please upload a valid PDF file!'
        except Exception as e:
            error = str(e)
    used, limit = get_usage('pdf_to_text') if current_user.is_authenticated else (0, LIMITS['free']['pdf_to_text'])
    return render_template('pdf_to_text.html', text=text, message=message, error=error, used=used, limit=limit)

# ============================================================
# TEXT TO PDF
# ============================================================
@app.route('/text-to-pdf', methods=['GET', 'POST'])
def text_to_pdf():
    message = ''
    error = ''
    if request.method == 'POST':
        text = ''
        try:
            if not check_limit('text_to_pdf'):
                used, limit = get_usage('text_to_pdf')
                error = f'Daily limit reached! Used {used}/{limit} files. Upgrade to Pro for more.'
            else:
                txt_file = request.files.get('txt_file')
                if txt_file and txt_file.filename != '':
                    text = txt_file.read().decode('utf-8', errors='replace')
                if not text:
                    text = request.form.get('text', '')
                if text.strip():
                    from reportlab.lib.pagesizes import A4
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                    from reportlab.lib.styles import ParagraphStyle
                    from reportlab.lib.units import mm
                    from reportlab.lib.enums import TA_LEFT
                    output_path = os.path.abspath(os.path.join(STATIC_FOLDER, 'output.pdf'))
                    doc = SimpleDocTemplate(output_path, pagesize=A4,
                        rightMargin=15*mm, leftMargin=15*mm,
                        topMargin=15*mm, bottomMargin=15*mm)
                    style = ParagraphStyle('custom', fontSize=11,
                        leading=16, wordWrap='LTR', alignment=TA_LEFT)
                    story = []
                    for line in text.split('\n'):
                        line = line.strip()
                        if line == '':
                            story.append(Spacer(1, 6))
                        else:
                            line = line.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                            while len(line) > 500:
                                story.append(Paragraph(line[:500], style))
                                line = line[500:]
                            story.append(Paragraph(line, style))
                    doc.build(story)
                    increment_usage('text_to_pdf')
                    message = 'success'
                else:
                    error = 'Text is empty!'
        except Exception as e:
            error = str(e)
    used, limit = get_usage('text_to_pdf') if current_user.is_authenticated else (0, LIMITS['free']['text_to_pdf'])
    return render_template('text_to_pdf.html', message=message, error=error, used=used, limit=limit)

# ============================================================
# IMAGE TO TEXT
# ============================================================
@app.route('/image-to-text', methods=['GET', 'POST'])
def image_to_text():
    text = ''
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            if not check_limit('image_to_text'):
                used, limit = get_usage('image_to_text')
                error = f'Daily limit reached! Used {used}/{limit} files. Upgrade to Pro for more.'
            else:
                import pytesseract
                from PIL import Image
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                file = request.files.get('image_file')
                if file:
                    path = os.path.join(UPLOAD_FOLDER, file.filename)
                    file.save(path)
                    img = Image.open(path)
                    text = pytesseract.image_to_string(img)
                    txt_path = os.path.join(STATIC_FOLDER, 'ocr.txt')
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    increment_usage('image_to_text')
                    message = 'success'
                else:
                    error = 'Please upload an image!'
        except Exception as e:
            error = str(e)
    used, limit = get_usage('image_to_text') if current_user.is_authenticated else (0, LIMITS['free']['image_to_text'])
    return render_template('image_to_text.html', text=text, message=message, error=error, used=used, limit=limit)

# ============================================================
# WORD TO PDF
# ============================================================
@app.route('/word-to-pdf', methods=['GET', 'POST'])
def word_to_pdf():
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            if not check_limit('word_to_pdf'):
                used, limit = get_usage('word_to_pdf')
                error = f'Daily limit reached! Used {used}/{limit} files. Upgrade to Pro for more.'
            else:
                file = request.files.get('word_file')
                if file and file.filename.endswith('.docx'):
                    path = os.path.join(UPLOAD_FOLDER, file.filename)
                    file.save(path)
                    output_path = os.path.abspath(os.path.join(STATIC_FOLDER, 'word_output.pdf'))
                    try:
                        from docx2pdf import convert
                        convert(path, output_path)
                    except Exception as e1:
                        from docx import Document
                        from reportlab.lib.pagesizes import A4
                        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                        from reportlab.lib.styles import ParagraphStyle
                        from reportlab.lib.units import mm
                        doc = Document(path)
                        text = '\n'.join([p.text for p in doc.paragraphs])
                        d = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
                        style = ParagraphStyle('custom', fontSize=11, leading=16)
                        story = []
                        for line in text.split('\n'):
                            line = line.strip()
                            if line:
                                line = line.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                                story.append(Paragraph(line, style))
                            else:
                                story.append(Spacer(1, 6))
                        d.build(story)
                    if os.path.exists(output_path):
                        increment_usage('word_to_pdf')
                        message = 'success'
                    else:
                        error = 'PDF was not created!'
                else:
                    error = 'Please upload a valid .docx file!'
        except Exception as e:
            error = str(e)
    used, limit = get_usage('word_to_pdf') if current_user.is_authenticated else (0, LIMITS['free']['word_to_pdf'])
    return render_template('word_to_pdf.html', message=message, error=error, used=used, limit=limit)

# ============================================================
# PDF TO WORD
# ============================================================
@app.route('/pdf-to-word', methods=['GET', 'POST'])
def pdf_to_word():
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            if not check_limit('pdf_to_word'):
                used, limit = get_usage('pdf_to_word')
                error = f'Daily limit reached! Used {used}/{limit} files. Upgrade to Pro for more.'
            else:
                from pdf2docx import Converter
                file = request.files.get('pdf_file')
                if file and file.filename.endswith('.pdf'):
                    pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
                    file.save(pdf_path)
                    docx_path = os.path.abspath(os.path.join(STATIC_FOLDER, 'output.docx'))
                    cv = Converter(pdf_path)
                    cv.convert(docx_path, start=0, end=None)
                    cv.close()
                    if os.path.exists(docx_path):
                        increment_usage('pdf_to_word')
                        message = 'success'
                    else:
                        error = 'File was not created!'
                else:
                    error = 'Please upload a valid PDF file!'
        except Exception as e:
            error = str(e)
    used, limit = get_usage('pdf_to_word') if current_user.is_authenticated else (0, LIMITS['free']['pdf_to_word'])
    return render_template('pdf_to_word.html', message=message, error=error, used=used, limit=limit)

# ============================================================
# TRANSLATOR
# ============================================================
@app.route('/translator', methods=['GET', 'POST'])
def translator():
    result = ''
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            text = request.form.get('text', '')
            word_count = len(text.split())
            if not check_limit('translator', word_count):
                used, limit = get_usage('translator')
                error = f'Daily limit reached! Used {used}/{limit} words. Upgrade to Pro for more.'
            else:
                from deep_translator import GoogleTranslator
                source = request.form.get('source', 'ur')
                target = request.form.get('target', 'en')
                if text.strip():
                    result = GoogleTranslator(source=source, target=target).translate(text)
                    increment_usage('translator', word_count)
                    message = 'success'
                else:
                    error = 'Please enter text!'
        except Exception as e:
            error = str(e)
    used, limit = get_usage('translator') if current_user.is_authenticated else (0, LIMITS['free']['translator'])
    return render_template('translator.html', result=result, message=message, error=error, used=used, limit=limit)

# ============================================================
# QR CODE GENERATOR
# ============================================================
@app.route('/qr-generator', methods=['GET', 'POST'])
def qr_generator():
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            if not check_limit('qr'):
                used, limit = get_usage('qr')
                error = f'Daily limit reached! Used {used}/{limit} QR codes. Upgrade to Pro for more.'
            else:
                import qrcode
                from PIL import Image, ImageDraw
                text = request.form.get('text', '')
                logo_file = request.files.get('logo_file')
                bg_file = request.files.get('bg_file')
                qr_color = request.form.get('qr_color', '#000000')
                bg_color = request.form.get('bg_color', '#ffffff')
                if text.strip():
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=15,
                        border=4,
                    )
                    qr.add_data(text)
                    qr.make(fit=True)
                    def hex_to_rgb(hex_color):
                        hex_color = hex_color.lstrip('#')
                        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    fill_color = hex_to_rgb(qr_color)
                    back_color = hex_to_rgb(bg_color)
                    qr_img = qr.make_image(
                        fill_color=fill_color,
                        back_color=back_color
                    ).convert('RGBA')
                    qr_width, qr_height = qr_img.size
                    if bg_file and bg_file.filename != '':
                        bg_path = os.path.join(UPLOAD_FOLDER, bg_file.filename)
                        bg_file.save(bg_path)
                        bg_img = Image.open(bg_path).convert('RGBA')
                        bg_img = bg_img.resize((qr_width, qr_height))
                        qr_array = qr_img.load()
                        for y in range(qr_height):
                            for x in range(qr_width):
                                r, g, b, a = qr_array[x, y]
                                if r > 200 and g > 200 and b > 200:
                                    qr_array[x, y] = (r, g, b, 120)
                                else:
                                    qr_array[x, y] = (r, g, b, 255)
                        qr_img = Image.alpha_composite(bg_img, qr_img)
                    if logo_file and logo_file.filename != '':
                        logo_path = os.path.join(UPLOAD_FOLDER, logo_file.filename)
                        logo_file.save(logo_path)
                        logo = Image.open(logo_path).convert('RGBA')
                        logo_size = qr_width // 5
                        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
                        bg_size = logo_size + 25
                        circle_bg = Image.new('RGBA', (bg_size, bg_size), (0, 0, 0, 0))
                        draw = ImageDraw.Draw(circle_bg)
                        draw.ellipse([0, 0, bg_size, bg_size], fill=(255, 255, 255, 255))
                        logo_pos = ((bg_size - logo_size) // 2, (bg_size - logo_size) // 2)
                        circle_bg.paste(logo, logo_pos, logo)
                        pos = ((qr_width - bg_size) // 2, (qr_height - bg_size) // 2)
                        qr_img.paste(circle_bg, pos, circle_bg)
                    final = qr_img.convert('RGB')
                    final.save(os.path.join(STATIC_FOLDER, 'qrcode.png'))
                    increment_usage('qr')
                    message = 'success'
                else:
                    error = 'Please enter text or URL!'
        except Exception as e:
            error = str(e)
    used, limit = get_usage('qr') if current_user.is_authenticated else (0, LIMITS['free']['qr'])
    return render_template('qr_generator.html', message=message, error=error, used=used, limit=limit)

# ============================================================
# IMAGE CONVERTER
# ============================================================
@app.route('/image-converter', methods=['GET', 'POST'])
def image_converter():
    message = ''
    error = ''
    output_file = ''
    if request.method == 'POST':
        try:
            if not check_limit('image'):
                used, limit = get_usage('image')
                error = f'Daily limit reached! Used {used}/{limit} images. Upgrade to Pro for more.'
            else:
                from PIL import Image
                file = request.files.get('image_file')
                fmt = request.form.get('format', 'PNG')
                if file:
                    path = os.path.join(UPLOAD_FOLDER, file.filename)
                    file.save(path)
                    output_file = f'converted.{fmt.lower()}'
                    output_path = os.path.join(STATIC_FOLDER, output_file)
                    img = Image.open(path)
                    if fmt == 'JPEG' and img.mode == 'RGBA':
                        img = img.convert('RGB')
                    img.save(output_path, fmt)
                    increment_usage('image')
                    message = 'success'
                else:
                    error = 'Please upload an image!'
        except Exception as e:
            error = str(e)
    used, limit = get_usage('image') if current_user.is_authenticated else (0, LIMITS['free']['image'])
    return render_template('image_converter.html', message=message, error=error, output_file=output_file, used=used, limit=limit)

# ============================================================
# DOWNLOADS
# ============================================================
@app.route('/download/<filename>')
def download(filename):
    allowed = [
        'output.mp3', 'output.pdf', 'extracted.txt',
        'word_output.pdf', 'qrcode.png', 'ocr.txt',
        'converted.png', 'converted.jpg', 'converted.webp',
        'converted.bmp', 'converted.ico', 'output.docx'
    ]
    if filename in allowed:
        path = os.path.abspath(os.path.join(STATIC_FOLDER, filename))
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
    return "File not found!", 404

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(port=5003, debug=True)
