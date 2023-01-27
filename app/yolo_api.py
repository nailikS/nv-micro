import io
import os
from flask import Flask, render_template, request, redirect, send_file, Response
from PIL import Image
import numpy as np
import cv2
import time
from cvu.detector.yolov5 import Yolov5 as Yolov5Onnx
import threading
import glob
from pathlib import Path

app = Flask(__name__)

last_request_time = time.time()
request_count = 0
process_start_time = str(time.time())

# load model
model = Yolov5Onnx(classes=['eye_open', 'eye_closed'],
                    backend="onnx",
                    weight='cpu',
                    device='best.onnx')

def clear_stored_images(interval_s=15, older_than_s=60):
    older_than_ns = older_than_s * 1000000000
    while True:
        current_time_ns = time.time_ns()
        cut_off_time_ns = current_time_ns - older_than_ns

        jpg_paths = glob.glob('static\\\[0-9]*.jpg')
        for jpg_path in jpg_paths:
            file_timestamp = int(Path(jpg_path).stem)
            if(cut_off_time_ns > file_timestamp):
                os.remove(jpg_path)

        time.sleep(interval_s)


clear_stored_images_thread = threading.Thread(target=clear_stored_images, daemon=True)
clear_stored_images_thread.start()

def detect_image(image, filename='static/0.jpg'):
    # inference
    preds = model(image)
    print(preds)

    # draw image
    preds.draw(image)

    # write image
    cv2.imwrite(filename, image)

@app.route('/', methods=['GET', 'POST'])
def process_request():
    global request_count

    request_count = request_count + 1
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files.get('file')
        if not file:
            return

        current_time_ns = time.time_ns()
        filename = 'static/' + str(current_time_ns) + '.jpg'

        img_bytes = file.read()
        opencvImage = cv2.cvtColor(np.array(Image.open(io.BytesIO(img_bytes))), cv2.COLOR_RGB2BGR) # dont know if necessary
        detect_image(opencvImage, filename=filename)
        #result.save(save_dir='static', exist_ok=True)

        return send_file(filename, mimetype='image/jpg')
    return render_template('index.html')


@app.route('/metrics')
def get_request_count():
    global last_request_time
    global request_count
    global process_start_time

    current_time = time.time()
    request_time_difference = time.time() - last_request_time
    last_request_time = current_time

    return_value = request_count / request_time_difference
    request_count = 0
    metrics_string = '# TYPE requests_per_s gauge\nrequests_per_s ' + str(return_value) + '\n\n'

    # get current unix timestamp
    metrics_string = metrics_string + '# TYPE process_start_time_seconds gauge\nprocess_start_time_seconds ' + process_start_time + '\n'
    
    return Response(metrics_string, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)