import asyncio
from app.llm import LanguageModelProcessor
from app.text_to_speech import TextToSpeech
from utils.audio_transcription import get_transcript, transcript_collector

class ConversationManager:
    def __init__(self):
        self.transcription_response = ""
        self.llm = LanguageModelProcessor()

    async def main(self):
        def handle_full_sentence(full_sentence):
            self.transcription_response = full_sentence

        while True:
            await get_transcript(handle_full_sentence)
            if "goodbye" in self.transcription_response.lower():
                break
            llm_response = self.llm.process(self.transcription_response)
            tts = TextToSpeech()
            tts.speak(llm_response)
            self.transcription_response = ""
