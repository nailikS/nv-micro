import io
from flask import Flask, render_template, request, redirect, send_file
from PIL import Image
import torch

app = Flask(__name__)

model = torch.hub.load('ultralytics/yolov5', 'custom', 'best.onnx')

@app.route('/', methods=['GET', 'POST'])
def process_request():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files.get('file')
        if not file:
            return

        img_bytes = file.read()
        result = model(Image.open(io.BytesIO(img_bytes)))
        result.save(save_dir='static', exist_ok=True)

        return send_file('static/image0.jpg', mimetype='image/jpg')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)