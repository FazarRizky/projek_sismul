from flask import Flask, request, render_template, send_from_directory
import os
import ffmpeg
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'static/output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['video']
        if file:
            # Simpan dengan nama unik
            unique_id = str(uuid.uuid4())
            filename = unique_id + "_" + file.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Output file paths
            mjpeg_filename = f"intraframe_{unique_id}.avi"
            mpeg_filename = f"interframe_{unique_id}.mp4"
            mjpeg_output = os.path.join(OUTPUT_FOLDER, mjpeg_filename)
            mpeg_output = os.path.join(OUTPUT_FOLDER, mpeg_filename)

            # Intraframe (MJPEG)
            ffmpeg.input(filepath).output(mjpeg_output, vcodec='mjpeg').run()

            # Interframe (MPEG4)
            ffmpeg.input(filepath).output(mpeg_output, vcodec='mpeg4').run()

            return render_template("index.html", mjpeg=mjpeg_filename, mpeg=mpeg_filename)

    return render_template("index.html", mjpeg=None, mpeg=None)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
