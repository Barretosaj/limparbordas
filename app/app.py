import os
from flask import Flask, request, send_file, render_template_string, jsonify
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
import time
import threading
from pathlib import Path

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'  # Corrigido para funcionar no Render

# Garante que as pastas existam
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Variável global para armazenar o progresso
processing_progress = 0
processing_active = False


def cm_to_pixels(cm, dpi=200):
    return int((cm / 2.54) * dpi)


def erase_image_borders_custom(img, superior_cm, inferior_cm, left_cm, right_cm, dpi=200):
    superior = cm_to_pixels(superior_cm, dpi)
    inferior = cm_to_pixels(inferior_cm, dpi)
    left = cm_to_pixels(left_cm, dpi)
    right = cm_to_pixels(right_cm, dpi)
    h, w = img.shape[:2]
    mask = np.ones_like(img) * 255
    img[0:superior, :] = mask[0:superior, :]
    img[h-inferior:h, :] = mask[h-inferior:h, :]
    img[:, 0:left] = mask[:, 0:left]
    img[:, w-right:w] = mask[:, w-right:w]
    return img


def process_pdf(pdf_path, output_pdf_path, superior_cm, inferior_cm, left_cm, right_cm):
    global processing_progress, processing_active

    processing_active = True
    processing_progress = 0

    try:
        images = convert_from_path(pdf_path, dpi=200)
        total_pages = len(images)
        cleaned_images = []

        for i, img in enumerate(images):
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            cleaned = erase_image_borders_custom(
                img_cv, superior_cm, inferior_cm, left_cm, right_cm)
            cleaned_pil = Image.fromarray(
                cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB))
            cleaned_images.append(cleaned_pil)

            processing_progress = int((i + 1) / total_pages * 100)
            time.sleep(0.1)

        cleaned_images[0].save(
            output_pdf_path, save_all=True, append_images=cleaned_images[1:])
        return True
    finally:
        processing_active = False


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>LIMPAR BORDAS DE PDF</title>
    <style>
        body {
            background-color: #f2f2f2;
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 40px;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 12px;
            max-width: 600px;
            margin: auto;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-transform: uppercase;
        }
        .upload-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin: 20px auto;
        }
        input[type="file"] {
            padding: 10px;
            flex: 1;
        }
        .loader-container {
            position: relative;
            width: 100px;
            height: 100px;
            margin: 20px auto;
        }
        .loader {
            width: 80px;
            height: 80px;
            border: 8px solid #f3f3f3;
            border-top: 8px solid #0ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        }
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-weight: bold;
            color: #007BFF;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        button {
            background-color: #007BFF;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
        }
        button:hover {
            background-color: #0056b3;
        }
        a.download-link {
            display: inline-block;
            margin-top: 30px;
            background-color: #28a745;
            color: white;
            padding: 10px 18px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: bold;
        }
        a.download-link:hover {
            background-color: #218838;
        }
        .form-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            margin-top: 20px;
        }
        .input-group {
            flex: 0 0 48%;
            margin-bottom: 15px;
            text-align: left;
        }
        .input-group label {
            display: block;
            margin-bottom: 5px;
        }
        .input-group input {
            width: 100%;
            padding: 8px;
        }
        .preview {
            width: 100px;
            height: 140px;
            background-color: white;
            border: 2px solid #ccc;
            margin: 20px auto;
            position: relative;
        }
        .preview::before,
        .preview::after {
            content: '';
            position: absolute;
            pointer-events: none;
        }
        .highlight-superior::before {
            top: 0; left: 0; right: 0;
            height: 15%;
            background-color: rgba(0, 255, 0, 0.3);
        }
        .highlight-inferior::before {
            bottom: 0; left: 0; right: 0;
            height: 15%;
            background-color: rgba(0, 255, 0, 0.3);
        }
        .highlight-left::after {
            top: 0; bottom: 0; left: 0;
            width: 15%;
            background-color: rgba(0, 255, 0, 0.3);
        }
        .highlight-right::after {
            top: 0; bottom: 0; right: 0;
            width: 15%;
            background-color: rgba(0, 255, 0, 0.3);
        }
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>LIMPAR BORDAS DE PDF</h1>
        <form id="uploadForm" method="post" enctype="multipart/form-data">
            <div class="upload-row">
                <input type="file" name="file" accept="application/pdf" required>
            </div>

            <div class="form-row">
                <div class="input-group">
                    <label for="superior">Superior (cm):</label>
                    <input type="number" name="superior" min="0" max="10" step="0.1" required>
                </div>
                <div class="input-group">
                    <label for="inferior">Inferior (cm):</label>
                    <input type="number" name="inferior" min="0" max="10" step="0.1" required>
                </div>
                <div class="input-group">
                    <label for="esquerda">Esquerda (cm):</label>
                    <input type="number" name="esquerda" min="0" max="10" step="0.1" required>
                </div>
                <div class="input-group">
                    <label for="direita">Direita (cm):</label>
                    <input type="number" name="direita" min="0" max="10" step="0.1" required>
                </div>
            </div>

            <div id="paper" class="preview"></div>

            <button type="submit">Enviar e Processar</button>
        </form>

        <div id="loaderContainer" class="loader-container hidden">
            <div class="loader"></div>
            <div id="progressText" class="progress-text">0%</div>
        </div>

        <div id="downloadSection">
            {% if download_link %}
                <a href="{{ download_link }}" class="download-link">Baixar PDF Limpo</a>
            {% endif %}
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const paper = document.getElementById('paper');
            const inputs = document.querySelectorAll('input[type=number]');
            const form = document.getElementById('uploadForm');
            const loaderContainer = document.getElementById('loaderContainer');
            const progressText = document.getElementById('progressText');
            const downloadSection = document.getElementById('downloadSection');

            inputs.forEach(input => {
                input.addEventListener('focus', () => {
                    const side = input.name;
                    paper.className = 'preview';
                    if (side === 'superior') paper.classList.add('highlight-superior');
                    if (side === 'inferior') paper.classList.add('highlight-inferior');
                    if (side === 'esquerda') paper.classList.add('highlight-left');
                    if (side === 'direita') paper.classList.add('highlight-right');
                });
            });

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                loaderContainer.classList.remove('hidden');
                downloadSection.innerHTML = '';
                
                const formData = new FormData(form);
                
                try {
                    const response = await fetch('/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const checkProgress = async () => {
                        const progressResponse = await fetch('/progress');
                        const progressData = await progressResponse.json();
                        
                        progressText.textContent = `${progressData.progress}%`;
                        
                       if (progressData.active) {
    setTimeout(checkProgress, 500);
} else {
    if (progressData.progress === 100) {
        // Vai diretamente para o link de download
        window.location.href = '/download/limpo_' + formData.get('file').name;
    }
}

                    };
                    
                    setTimeout(checkProgress, 500);
                    
                } catch (error) {
                    console.error('Error:', error);
                }
            });
        });
    </script>
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global processing_progress, processing_active

    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            output_filename = f'limpo_{filename}'
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            file.save(input_path)

            superior = float(request.form.get('superior', 2))
            inferior = float(request.form.get('inferior', 2))
            esquerda = float(request.form.get('esquerda', 2))
            direita = float(request.form.get('direita', 2))

            thread = threading.Thread(
                target=process_pdf,
                args=(input_path, output_path, superior,
                      inferior, esquerda, direita)
            )
            thread.start()

            return render_template_string(HTML_TEMPLATE, download_link=f'/download/{output_filename}')

    return render_template_string(HTML_TEMPLATE, download_link=None)


@app.route('/progress')
def get_progress():
    global processing_progress, processing_active
    return jsonify({
        'progress': processing_progress,
        'active': processing_active
    })


@app.route('/download/<filename>')
def download_file(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)

    if not os.path.exists(path):
        return "Arquivo não encontrado", 404

    return send_file(
        path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )


if __name__ == '__main__':
    app.run(debug=True)
