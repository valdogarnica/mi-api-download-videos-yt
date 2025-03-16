from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import json
from moviepy import VideoFileClip # En lugar de VideoFileClip
from moviepy import AudioFileClip 
from flask_socketio import SocketIO, emit




import urllib.parse

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Habilita WebSockets
# Habilitar CORS si tu app de Android hace peticiones a este servidor
from flask_cors import CORS
CORS(app)

# Carpeta donde se guardarán los videos descargados
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

DOWNLOAD_MUSICA = "downloads_musica"
os.makedirs(DOWNLOAD_MUSICA, exist_ok=True)

def progress_hook(d):
    if d['status'] == 'downloading':
        progress_msg = f"Descargando: {d['_percent_str']} - {d['_speed_str']} - {d['_eta_str']} restantes"
        print(progress_msg)  # Mostrar en consola del servidor
        socketio.emit("download_progress", {"message": progress_msg})  # Enviar a la app

@app.route("/get_video_info", methods=["GET"])
def get_video_info():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Falta la URL"}), 400

    ydl_opts = {"quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = [
            {"format_id": f["format_id"], "ext": f["ext"], "url": f["url"], "resolution": f.get("resolution", "unknown")}
            for f in info.get("formats", [])
        ]
    
    return jsonify({"title": info["title"], "formats": formats})

@app.route("/download_video", methods=["POST"])
def download_video():
    data = request.json
    url = data.get("url")
    format_id = data.get("format_id")

    if not url or not format_id:
        return jsonify({"error": "Faltan parámetros"}), 400

    ydl_opts = {
        "format": format_id,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        #video_path = os.path.join(DOWNLOAD_FOLDER, f"{info['title']}.{info['ext']}")
        video_path = f"{info['id']}.{info['ext']}"
        print("video path: ", video_path)

    response = jsonify({
        "success": True,
        "status_code": 200,
        "message": "Descarga completada",
        "file_path": video_path
        })
    print(response.status_code)
    response_data = json.loads(response.get_data(as_text=True))
    print("print final ",response_data)
    return response

@app.route("/download_audio", methods=["POST"])
def download_audio():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "Falta el parámetro 'url' en la solicitud"}), 400

    url = data["url"]
    format_id = "bestaudio/best"

    ydl_opts = {
        "format": format_id,
        "outtmpl": f"{DOWNLOAD_MUSICA}/%(id)s.%(ext)s",
        "progress_hooks": [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = os.path.join(DOWNLOAD_MUSICA, f"{info['id']}.{info['ext']}")
            audio_path = os.path.join(DOWNLOAD_MUSICA, f"{info['id']}.mp3")
            ruta_audio = f"{info['id']}.mp3"

        # Convertir con moviepy
        try:
            audio = AudioFileClip(video_path)
            audio.write_audiofile(audio_path)
            audio.close()
            os.remove(video_path)  # Eliminar el archivo de video después de la conversión
        except Exception as e:
            return jsonify({"error": f"Error al convertir con moviepy: {str(e)}"}), 500

        return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Descarga y conversión completadas",
            "file_path": ruta_audio
        })

    except Exception as e:
        return jsonify({"error": f"Error en el proceso: {str(e)}"}), 500

@app.route("/get_download/<filename>", methods=["GET"])
def get_download(filename):
    #decoded_file = urllib.parse.unquote(filename)
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    print(file_path)
    print(file_path)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "Archivo no encontrado"}), 404

@app.route("/get_download_music/<filename>", methods=["GET"])
def get_download_music(filename):
    #decoded_file = urllib.parse.unquote(filename)
    file_path = os.path.join(DOWNLOAD_MUSICA, filename)
    print(file_path)
    print(file_path)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "Archivo no encontrado"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)