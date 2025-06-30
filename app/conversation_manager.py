import asyncio
import sys
import json
import subprocess # For tts process wait timeout
from app.llm import LanguageModelProcessor
from app.text_to_speech import TextToSpeech
from utils.audio_transcription import get_transcript, stop_transcription # Import stop_transcription

class ConversationManager:
    def __init__(self, electron_communication=False):
        self.transcription_response = ""
        self.llm = LanguageModelProcessor()
        self.tts = TextToSpeech()
        self.electron_communication = electron_communication
        self.stop_requested = False
        self.transcription_complete = asyncio.Event()
        self.current_transcription_task = None


    def _send_to_electron(self, type, content):
        if self.electron_communication:
            message = json.dumps({"type": type, "content": content})
            print(message, flush=True)

    async def _handle_full_sentence_electron(self, full_sentence):
        self.transcription_response = full_sentence
        if not self.stop_requested: # Only send if not in the process of stopping
            self._send_to_electron("thought", f"Heard: {full_sentence}")
        self.transcription_complete.set()

    async def _get_transcript_async_electron(self):
        self.transcription_response = ""
        self.transcription_complete.clear()

        # We pass the async callback directly to get_transcript
        self.current_transcription_task = asyncio.create_task(get_transcript(self._handle_full_sentence_electron))

        try:
            await self.transcription_complete.wait()
        except asyncio.CancelledError:
            # This occurs if request_stop cancels current_transcription_task while waiting
            self._send_to_electron("status", "transcription_cancelled")
            return "" # Return empty if cancelled
        finally:
            if self.current_transcription_task and not self.current_transcription_task.done():
                self.current_transcription_task.cancel() # Ensure it's cancelled if we exit wait early for other reasons

        return self.transcription_response


    async def main_electron(self):
        self.stop_requested = False # Reset stop request at the beginning of a new cycle
        self._send_to_electron("status", "listening")

        user_input = await self._get_transcript_async_electron()

        if self.stop_requested: # Check if stop was requested during transcription
            self._send_to_electron("status", "interrupted_during_transcription")
            return

        if not user_input and not self.stop_requested: # Handle empty transcription if not due to stop
            self._send_to_electron("status", "no_input_detected")
            # self._send_to_electron("status", "ready_to_listen") # Go back to ready
            return

        if "goodbye" in user_input.lower():
            self._send_to_electron("status", "goodbye_detected")
            self.tts.speak("Goodbye!")
            self._send_to_electron("status", "ended")
            return

        self._send_to_electron("status", "thinking")
        # Ensure LLM processing is not blocking excessively or can be made async
        llm_response = await asyncio.to_thread(self.llm.process, user_input)


        if self.stop_requested:
            self._send_to_electron("status", "interrupted_before_speech")
            return

        self._send_to_electron("status", "speaking")
        self._send_to_electron("thought", llm_response)

        await asyncio.to_thread(self.tts.speak, llm_response)

        if self.stop_requested:
            self._send_to_electron("status", "interrupted_during_speech")
            # TTS stopping is handled in request_stop
            return

        # If not stopped and not goodbye, prepare for next interaction
        if not self.stop_requested:
            self._send_to_electron("status", "ready_to_listen")


    # Original main for non-Electron use
    async def main(self):
        # This synchronous callback is fine for the original main,
        # as get_transcript would block until full sentence or is made async.
        def handle_full_sentence_sync(full_sentence):
            self.transcription_response = full_sentence

        while not self.stop_requested:
            # Assuming the original get_transcript was blocking or adapted to set a sync flag.
            # For this example, let's assume it's an async version for consistency.
            await get_transcript(handle_full_sentence_sync) # Needs to be an async version

            if self.stop_requested: break
            if "goodbye" in self.transcription_response.lower():
                self.tts.speak("Goodbye!")
                break

            llm_response = self.llm.process(self.transcription_response)
            if self.stop_requested: break
            self.tts.speak(llm_response)
            self.transcription_response = ""

    async def request_stop(self):
        self.stop_requested = True

        # Signal audio_transcription to stop
        await stop_transcription()

        if self.current_transcription_task and not self.current_transcription_task.done():
            self.current_transcription_task.cancel()
        self.transcription_complete.set() # Unblock _get_transcript_async_electron if it's waiting

        # Stop TTS
        if hasattr(self.tts, 'stop') and callable(self.tts.stop):
            self.tts.stop()
        elif hasattr(self.tts, 'process') and self.tts.process:
            if self.tts.process.poll() is None:
                self.tts.process.terminate()
                try:
                    self.tts.process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    self.tts.process.kill()
                    self.tts.process.wait()
        self._send_to_electron("status", "stop_requested_processed")


if __name__ == '__main__':
    manager = ConversationManager()
    try:
        asyncio.run(manager.main())
    except KeyboardInterrupt:
        print("Conversation ended by user.")
    finally:
        # Ensure TTS is stopped on exit for direct script run
        if hasattr(manager.tts, 'stop') and callable(manager.tts.stop):
            manager.tts.stop()
        elif hasattr(manager.tts, 'process') and manager.tts.process and manager.tts.process.poll() is None:
             manager.tts.process.terminate()
             manager.tts.process.wait()
