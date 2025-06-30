import asyncio
import os
from dotenv import load_dotenv
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions, Microphone
from app.transcript_collector import transcript_collector

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Global state for microphone and connection management
microphone = None
dg_connection = None
stop_event = asyncio.Event() # Used to signal transcription to stop

async def get_transcript(callback):
    """
    Captures audio from the microphone, transcribes it using Deepgram,
    and calls the callback with the final transcript.
    This function is designed to be called for each new transcription session.
    """
    global microphone, dg_connection
    transcription_complete = asyncio.Event()
    stop_event.clear() # Clear stop event at the beginning of a new session

    try:
        config = DeepgramClientOptions(options={"keepalive": "true"})
        deepgram: DeepgramClient = DeepgramClient(DEEPGRAM_API_KEY, config)
        dg_connection = deepgram.listen.asynclive.v("1")
        # print("DEBUG: Deepgram connection created.") # Debug print

        async def on_message(self, result, **kwargs):
            # print(f"DEBUG: Deepgram on_message: {result}") # Debug print
            sentence = result.channel.alternatives[0].transcript
            if not result.speech_final:
                transcript_collector.add_part(sentence)
            else:
                transcript_collector.add_part(sentence)
                full_sentence = transcript_collector.get_full_transcript()
                if len(full_sentence.strip()) > 0:
                    full_sentence = full_sentence.strip()
                    # print(f"DEBUG: User: {full_sentence}") # Debug print
                    # Ensure callback is awaited if it's an async function
                    if asyncio.iscoroutinefunction(callback):
                        await callback(full_sentence)
                    else:
                        callback(full_sentence)
                    transcript_collector.reset()
                    transcription_complete.set() # Signal that this transcription is done

        async def on_error(self, error, **kwargs):
            # print(f"DEBUG: Deepgram error: {error}") # Debug print
            # Signal completion to unblock, maybe with an error indicator if callback supports it
            transcription_complete.set()
            # Consider how to propagate this error or if just logging is enough

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)


        options = LiveOptions(
            model="nova-2",
            punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            endpointing=300, # Milliseconds of silence to consider an utterance complete
            smart_format=True,
        )

        # print("DEBUG: Starting Deepgram connection...") # Debug print
        await dg_connection.start(options)

        # Create and start microphone instance for this session
        microphone = Microphone(dg_connection.send)
        # print("DEBUG: Microphone created.") # Debug print
        microphone.start()
        # print("DEBUG: Microphone started. Waiting for transcription or stop signal...") # Debug print

        # Wait for either transcription to complete or an external stop signal
        await asyncio.wait(
            [transcription_complete.wait(), stop_event.wait()],
            return_when=asyncio.FIRST_COMPLETED
        )
        # print("DEBUG: Wait completed. Transcription complete or stop signaled.") # Debug print

    except Exception as e:
        # print(f"DEBUG: Error in get_transcript: {e}") # Debug print
        # Ensure transcription_complete is set to avoid deadlocks if an error occurs early
        transcription_complete.set()
    finally:
        # print("DEBUG: Cleaning up transcription resources...") # Debug print
        if microphone:
            # print("DEBUG: Stopping microphone...") # Debug print
            microphone.finish()
            microphone = None # Reset for next call
            # print("DEBUG: Microphone stopped and reset.") # Debug print
        if dg_connection:
            # print("DEBUG: Closing Deepgram connection...") # Debug print
            await dg_connection.finish()
            dg_connection = None # Reset for next call
            # print("DEBUG: Deepgram connection closed and reset.") # Debug print
        # print("DEBUG: Transcription cleanup finished.") # Debug print


async def stop_transcription():
    """
    Signals the ongoing transcription process to stop.
    """
    # print("DEBUG: stop_transcription called.") # Debug print
    stop_event.set()
    # The rest of the cleanup is handled in get_transcript's finally block.
    # Ensure this function is callable from ConversationManager's request_stop
    # This might involve passing the stop_event or making this function accessible.
