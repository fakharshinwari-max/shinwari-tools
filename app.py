from flask import Flask, render_template, request, send_file, jsonify
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = None

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'

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
                text = re.sub(r'[*#@&^%$~`<>|\\]', '', text)
                text = re.sub(r'\s+', ' ', text)
                tts = gTTS(text=text, lang=lang)
                tts.save(os.path.join(STATIC_FOLDER, 'output.mp3'))
                message = 'success'
            else:
                error = 'Text is empty!'
        except Exception as e:
            error = str(e)
    return render_template('urdu_tts.html', message=message, error=error)

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
                message = 'success'
            else:
                error = 'Please upload a valid PDF file!'
        except Exception as e:
            error = str(e)
    return render_template('pdf_to_text.html', text=text, message=message, error=error)

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
                message = 'success'
            else:
                error = 'Text is empty!'
        except Exception as e:
            error = str(e)
    return render_template('text_to_pdf.html', message=message, error=error)

# ============================================================
# IMAGE TO TEXT (OCR)
# ============================================================
@app.route('/image-to-text', methods=['GET', 'POST'])
def image_to_text():
    text = ''
    message = ''
    error = ''
    if request.method == 'POST':
        try:
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
                message = 'success'
            else:
                error = 'Please upload an image!'
        except Exception as e:
            error = str(e)
    return render_template('image_to_text.html', text=text, message=message, error=error)

# ============================================================
# WORD TO PDF
# ============================================================
@app.route('/word-to-pdf', methods=['GET', 'POST'])
def word_to_pdf():
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            from docx import Document
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.units import mm

            file = request.files.get('word_file')
            if file and file.filename.endswith('.docx'):
                path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(path)
                doc = Document(path)
                text = '\n'.join([para.text for para in doc.paragraphs])
                output_path = os.path.abspath(os.path.join(STATIC_FOLDER, 'word_output.pdf'))
                style = ParagraphStyle('custom', fontSize=11, leading=16)
                story = []
                d = SimpleDocTemplate(output_path, pagesize=A4,
                    rightMargin=15*mm, leftMargin=15*mm,
                    topMargin=15*mm, bottomMargin=15*mm)
                for line in text.split('\n'):
                    line = line.strip()
                    if line == '':
                        story.append(Spacer(1, 6))
                    else:
                        line = line.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                        story.append(Paragraph(line, style))
                d.build(story)
                message = 'success'
            else:
                error = 'Please upload a .docx file!'
        except Exception as e:
            error = str(e)
    return render_template('word_to_pdf.html', message=message, error=error)

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
            from deep_translator import GoogleTranslator
            text = request.form.get('text', '')
            source = request.form.get('source', 'ur')
            target = request.form.get('target', 'en')
            if text.strip():
                result = GoogleTranslator(source=source, target=target).translate(text)
                message = 'success'
            else:
                error = 'Please enter text!'
        except Exception as e:
            error = str(e)
    return render_template('translator.html', result=result, message=message, error=error)

# ============================================================
# QR CODE GENERATOR
# ============================================================
@app.route('/qr-generator', methods=['GET', 'POST'])
def qr_generator():
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            import qrcode
            text = request.form.get('text', '')
            if text.strip():
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(text)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(os.path.join(STATIC_FOLDER, 'qrcode.png'))
                message = 'success'
            else:
                error = 'Please enter text or URL!'
        except Exception as e:
            error = str(e)
    return render_template('qr_generator.html', message=message, error=error)

# ============================================================
# IMAGE CONVERTER
# ============================================================
@app.route('/image-converter', methods=['GET', 'POST'])
def image_converter():
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            from PIL import Image
            file = request.files.get('image_file')
            fmt = request.form.get('format', 'PNG')
            if file:
                path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(path)
                img = Image.open(path)
                output_path = os.path.join(STATIC_FOLDER, f'converted.{fmt.lower()}')
                if fmt == 'JPEG' and img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(output_path, fmt)
                message = 'success'
            else:
                error = 'Please upload an image!'
        except Exception as e:
            error = str(e)
    return render_template('image_converter.html', message=message, error=error)

# ============================================================
# PDF TO WORD
# ============================================================
@app.route('/pdf-to-word', methods=['GET', 'POST'])
def pdf_to_word():
    message = ''
    error = ''
    if request.method == 'POST':
        try:
            from pdf2docx import Converter
            file = request.files.get('pdf_file')
            if file and file.filename.endswith('.pdf'):
                pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(pdf_path)
                docx_path = os.path.abspath(
                    os.path.join(STATIC_FOLDER, 'output.docx')
                )
                cv = Converter(pdf_path)
                cv.convert(docx_path, start=0, end=None)
                cv.close()
                if os.path.exists(docx_path):
                    print(f"DOCX created! Size: {os.path.getsize(docx_path)} bytes")
                    message = 'success'
                else:
                    error = 'File was not created!'
            else:
                error = 'Please upload a valid PDF file!'
        except Exception as e:
            error = str(e)
            print(f"ERROR: {e}")
    return render_template('pdf_to_word.html', message=message, error=error)
# ============================================================
# DOWNLOADS
# ============================================================
@app.route('/download/<filename>')
def download(filename):
    allowed = [
    'output.mp3', 'output.pdf', 'extracted.txt',
    'word_output.pdf', 'qrcode.png', 'ocr.txt',
    'converted.png', 'converted.jpg', 'converted.webp',
    'output.docx'  # add this line
]
    if filename in allowed:
        path = os.path.abspath(os.path.join(STATIC_FOLDER, filename))
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
    return "File not found!", 404

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    app.run(port=5003, debug=True)
