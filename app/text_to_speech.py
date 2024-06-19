import os
import requests
import time
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO
import shutil

load_dotenv()

class TextToSpeech:
    DG_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    MODEL_NAME = "aura-luna-en"

    @staticmethod
    def is_installed(lib_name: str) -> bool:
        lib = shutil.which(lib_name)
        return lib is not None

    def speak(self, text):
        DEEPGRAM_URL = f"https://api.deepgram.com/v1/speak?model={self.MODEL_NAME}&performance=some&encoding=linear16&sample_rate=24000"
        headers = {
            "Authorization": f"Token {self.DG_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text
        }
        
        start_time = time.time()
        first_byte_time = None
        
        audio_buffer = BytesIO()
        
        with requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload) as r:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    if first_byte_time is None:
                        first_byte_time = time.time()
                        ttfb = int((first_byte_time - start_time) * 1000)
                        print(f"TTS Time to First Byte (TTFB): {ttfb}ms\n")
                    audio_buffer.write(chunk)
        
        audio_buffer.seek(0)
        audio_segment = AudioSegment.from_file(audio_buffer, format="wav")
        play(audio_segment)
