# Speech-to-Text Implementation for Prompt-Toolkit Terminal Agent

```python
import os
import time
import threading
import tempfile
import wave
import json
import pyaudio
import numpy as np
import requests
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.application import run_in_terminal

# Groq API configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
WHISPER_ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3"  # Available models: whisper-large-v3, whisper-large-v3-turbo, distil-whisper

# Audio recording settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 500  # Adjust based on your microphone sensitivity
SILENCE_DURATION = 5  # Seconds of silence to stop recording

# Global variables
recording = False
stop_recording = False
audio_frames = []

class AudioRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.stop_flag = False
        self.silence_count = 0
        self.temp_file = None
    
    def is_silent(self, data):
        """Check if the audio chunk is silent."""
        audio_data = np.frombuffer(data, dtype=np.int16)
        rms = np.sqrt(np.mean(np.square(audio_data)))
        return rms < SILENCE_THRESHOLD
    
    def record(self):
        """Start recording audio with silence detection."""
        self.frames = []
        self.is_recording = True
        self.stop_flag = False
        self.silence_count = 0
        
        try:
            self.stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            print("🎤 Recording... (silent periods will end recording)")
            
            while not self.stop_flag:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
                
                # Check for silence
                if self.is_silent(data):
                    self.silence_count += CHUNK / RATE
                    if self.silence_count >= SILENCE_DURATION:
                        print("🔇 Silence detected, stopping recording...")
                        break
                else:
                    self.silence_count = 0
            
            print("✅ Recording finished.")
            
            # Close the stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            # Save audio to temp file
            self.temp_file = self._save_to_temp_file()
            return self.temp_file
            
        except Exception as e:
            print(f"Error during recording: {e}")
            if self.stream:
                self.stream.close()
                self.stream = None
            return None
    
    def stop(self):
        """Stop the recording."""
        self.stop_flag = True
        self.is_recording = False
    
    def _save_to_temp_file(self):
        """Save recorded audio to a temporary WAV file."""
        fd, temp_path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.frames))
        
        return temp_path
    
    def cleanup(self):
        """Clean up resources."""
        if self.stream:
            self.stream.close()
        self.p.terminate()
        if self.temp_file and os.path.exists(self.temp_file):
            os.remove(self.temp_file)

class GroqWhisperTranscriber:
    def __init__(self, api_key):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set. Please set it as an environment variable.")
    
    def transcribe(self, audio_file_path):
        """Transcribe audio file using Groq's Whisper API."""
        if not os.path.exists(audio_file_path):
            print(f"Error: Audio file not found at {audio_file_path}")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        with open(audio_file_path, 'rb') as f:
            files = {
                'file': (os.path.basename(audio_file_path), f, 'audio/wav'),
                'model': (None, WHISPER_MODEL),
                'response_format': (None, 'json')
            }
            
            print("🔄 Transcribing audio with Groq Whisper...")
            response = requests.post(
                WHISPER_ENDPOINT,
                headers=headers,
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('text', '')
        else:
            print(f"Error in transcription: {response.status_code}")
            print(response.text)
            return None

class VoiceInputHandler:
    def __init__(self, session):
        self.session = session
        self.recorder = AudioRecorder()
        self.transcriber = GroqWhisperTranscriber(GROQ_API_KEY)
        self.recording_thread = None
    
    def start_voice_input(self):
        """Start recording voice input in a separate thread."""
        if self.recording_thread and self.recording_thread.is_alive():
            print("Already recording. Please wait.")
            return
        
        def record_and_transcribe():
            try:
                audio_file = self.recorder.record()
                if audio_file:
                    transcript = self.transcriber.transcribe(audio_file)
                    if transcript:
                        # Submit the transcript to prompt-toolkit
                        run_in_terminal(lambda: self._insert_text(transcript))
            except Exception as e:
                print(f"Error in voice recording/transcription: {e}")
            finally:
                # Clean up temporary file
                self.recorder.cleanup()
        
        self.recording_thread = threading.Thread(target=record_and_transcribe)
        self.recording_thread.daemon = True
        self.recording_thread.start()
    
    def _insert_text(self, text):
        """Insert text into prompt-toolkit and submit it."""
        # Clear current input
        current_buffer = self.session.default_buffer
        current_buffer.text = ""
        
        # Insert transcribed text
        current_buffer.insert_text(text)
        
        # Submit the input
        self.session.app.current_buffer.validate_and_handle()

def setup_voice_command(session):
    """Set up key bindings for voice command."""
    kb = KeyBindings()
    voice_handler = VoiceInputHandler(session)
    
    @kb.add('/voice')
    def _(event):
        """Start voice recording when '/voice' is typed."""
        # Clear the '/voice' command
        event.current_buffer.text = ""
        
        # Start voice recording
        voice_handler.start_voice_input()
    
    return kb

def main():
    """Main function to run the voice-enabled prompt-toolkit terminal."""
    # Create a session with custom key bindings for voice commands
    session = PromptSession()
    
    # Set up voice command handling
    kb = setup_voice_command(session)
    
    # Start the interactive prompt
    print("🎙️ Voice-enabled terminal")
    print("Type '/voice' to start recording. Speak and pause for 5 seconds to submit.")
    
    while True:
        try:
            text = session.prompt("> ", key_bindings=kb)
            print(f"You entered: {text}")
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

if __name__ == "__main__":
    main()
```

## How It Works

1. **Voice Recording Trigger**: Type `/voice` in the prompt-toolkit terminal to start recording.

2. **Recording Process**:
   - The system records audio from your microphone
   - Continuously monitors for silence
   - Automatically stops recording when 5 seconds of silence is detected

3. **Transcription**:
   - Recorded audio is saved to a temporary file
   - Sent to Groq's Whisper API for transcription
   - Transcription result is received as text

4. **Prompt-Toolkit Integration**:
   - Transcribed text is programmatically inserted into the prompt-toolkit input buffer
   - The input is automatically submitted

## Requirements

- Python 3.7+
- `prompt-toolkit`
- `pyaudio`
- `numpy`
- `requests`
- Groq API key (set as environment variable `GROQ_API_KEY`)

## References

1. [Python Prompt Toolkit Documentation](https://python-prompt-toolkit.readthedocs.io/)
   - Used for understanding the prompt-toolkit API and how to programmatically submit input

2. [Groq Automatic Speech Recognition (ASR) API](https://groq.com/GroqDocs/Groq%20ASR%20Model%20Guide.pdf)
   - Details about Whisper model options, rate limits, and API specifications

3. [Groq Whisperer Project](https://github.com/KennyVaneetvelde/groq_whisperer)
   - Used as reference for integrating Groq's Whisper implementation with Python applications

4. [GroqCloud Speech-to-Text Documentation](https://console.groq.com/docs/speech-text)
   - API endpoint details and response format information

5. [Python PyAudio Library with Silence Detection](https://stackoverflow.com/questions/68107245/how-to-detect-silence-with-pyaudio)
   - Techniques for implementing silence detection with PyAudio

6. [Prompt-Toolkit Key Bindings](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html)
   - Implementation details for custom key bindings in prompt-toolkit

7. [Audio RMS Calculation for Silence Detection](https://github.com/openvpi/audio-slicer)
   - Methods for calculating RMS to detect silent portions of audio

8. [Prompt-Toolkit's run_in_terminal](https://github.com/prompt-toolkit/python-prompt-toolkit/blob/master/src/prompt_toolkit/shortcuts/prompt.py)
   - Reference for safely interacting with the terminal from background threads
