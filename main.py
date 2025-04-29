import sounddevice as sd
import numpy as np
import wave 
import time
import requests
import os
from pydub import AudioSegment
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

SAMPLERATE = 44100 
CHANNELS = 2
CHUCK_SECONDS = 600 # 10 minutes
SERVER_URL = os.getenv("SERVER")
TEMP_DIR = os.getenv("DIR")
KEY_FILE = os.path.join(TEMP_DIR, "key.key")

#* Generate key once
if not os.path.exists(KEY_FILE):
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)
        
else: 
    with open(KEY_FILE, 'rb') as f:
        key = f.read()
        
cipher = Fernet(key)

def recorder():
    audio = sd.rec(int(CHUCK_SECONDS * SAMPLERATE), samplerate = SAMPLERATE, channels = CHANNELS, dtype = 'int16')
    sd.wait()
    return audio

def save_wave(filename, data):
    with wave.open(filename, 'wb') as wf:
        wf.setchannels(CHANNELS)
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
        response = requests.post(SERVER_URL, files=files)
    return response.status_code == 200

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
        
        if send_to_server(enc_path):
            os.remove(wan_path)
            os.remove(mp3_path)
            os.remove(enc_path)
            
    except Exception as e:
        with open(os.path.join(TEMP_DIR, "recorder_error.log"), 'a') as log:
            log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {str(e)}\n")
            
if __name__ == "__main__":
    main()