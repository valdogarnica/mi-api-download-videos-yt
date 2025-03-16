from moviepy import AudioFileClip 
import os
from flask import Flask, request, jsonify, send_file



DOWNLOAD_MUSICA = "downloads_musica"
os.makedirs(DOWNLOAD_MUSICA, exist_ok=True)
# Descargar solo el audio
@app.route("/download_audio", methods=["GET"])
def download_audio():
    url = request.args.get("url")

    if not url:
        return jsonify({"error": "Falta el parámetro 'url'"}), 400

    format_id = "bestaudio/best"

    ydl_opts = {
        "format": format_id,
        "outtmpl": f"{DOWNLOAD_MUSICA}/%(id)s.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = os.path.join(DOWNLOAD_MUSICA, f"{info['id']}.{info['ext']}")
            audio_path = os.path.join(DOWNLOAD_MUSICA, f"{info['id']}.mp3")

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
            "file_path": audio_path
        })

    except Exception as e:
        return jsonify({"error": f"Error en el proceso: {str(e)}"}), 500