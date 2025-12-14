#!/usr/bin/env python3
"""
Voice Recognition Test Script

Tests voice recognition independently using:
1. AssemblyAI API (online, high accuracy)
2. SpeechRecognition with Sphinx (offline)
"""

import sys
import os
import time

# Import required libraries
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("❌ SpeechRecognition not available")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("❌ Requests not available")

# AssemblyAI API key
ASSEMBLYAI_API_KEY = "0d558908be2a475facbc374a6d507860"

def transcribe_with_assemblyai(audio_data):
    """Transcribe audio using AssemblyAI API."""
    if not REQUESTS_AVAILABLE:
        return None

    try:
        print("📤 Uploading to AssemblyAI...")
        # Convert audio to WAV format
        wav_data = audio_data.get_wav_data(convert_rate=16000, convert_width=2)

        # Upload to AssemblyAI
        headers = {"authorization": ASSEMBLYAI_API_KEY}
        upload_response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=wav_data,
            timeout=30
        )

        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            return None

        upload_url = upload_response.json()["upload_url"]
        print("✅ Upload successful")

        # Request transcription
        print("🎯 Requesting transcription...")
        transcript_request = {
            "audio_url": upload_url,
            "language_code": "en"
        }

        transcript_response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers=headers,
            json=transcript_request,
            timeout=30
        )

        if transcript_response.status_code != 200:
            print(f"❌ Transcript request failed: {transcript_response.status_code}")
            return None

        transcript_id = transcript_response.json()["id"]
        print(f"📝 Transcript ID: {transcript_id}")

        # Poll for result
        print("⏳ Processing...")
        polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

        for i in range(30):  # Max 30 seconds
            poll_response = requests.get(polling_endpoint, headers=headers, timeout=10)
            result = poll_response.json()

            if result["status"] == "completed":
                text = result.get("text", "").strip()
                if text:
                    print(f"✅ AssemblyAI Result: '{text}'")
                    return text
                return None
            elif result["status"] == "error":
                print(f"❌ AssemblyAI error: {result.get('error')}")
                return None

            time.sleep(1)
            print(f"⏳ Waiting... ({i+1}/30)")

        print("❌ AssemblyAI polling timeout")
        return None

    except Exception as e:
        print(f"❌ AssemblyAI error: {e}")
        return None

def test_assemblyai():
    """Test voice recognition with AssemblyAI API."""
    print("\n" + "="*50)
    print("🎙️  TESTING ASSEMBLYAI (Online, High Accuracy)")
    print("="*50)

    if not SR_AVAILABLE:
        print("❌ SpeechRecognition not available")
        return

    if not REQUESTS_AVAILABLE:
        print("❌ Requests not available for AssemblyAI")
        return

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.0

    try:
        with sr.Microphone(sample_rate=16000) as source:
            print("🎤 Calibrating for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold: {recognizer.energy_threshold}")

            print("🎤 Speak now! (Recording for up to 10 seconds)")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            print(f"✅ Audio captured: {len(audio.get_raw_data())} bytes")

        print("⚙️ Transcribing with AssemblyAI...")
        result = transcribe_with_assemblyai(audio)

        if result:
            print(f"🎉 SUCCESS: '{result}'")
        else:
            print("❌ No transcription result")

    except sr.WaitTimeoutError:
        print("❌ Timeout - no speech detected")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_offline():
    """Test voice recognition with Sphinx (offline)."""
    print("\n" + "="*50)
    print("🎙️  TESTING SPHINX (Offline)")
    print("="*50)

    if not SR_AVAILABLE:
        print("❌ SpeechRecognition not available")
        return

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.0

    try:
        with sr.Microphone(sample_rate=16000) as source:
            print("🎤 Calibrating for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold: {recognizer.energy_threshold}")

            print("🎤 Speak now! (Recording for up to 10 seconds)")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            print(f"✅ Audio captured: {len(audio.get_raw_data())} bytes")

        print("⚙️ Transcribing with Sphinx (offline)...")
        result = recognizer.recognize_sphinx(audio)
        print(f"🎉 SUCCESS: '{result}'")

    except sr.WaitTimeoutError:
        print("❌ Timeout - no speech detected")
    except sr.UnknownValueError:
        print("❌ Could not understand audio")
    except sr.RequestError as e:
        print(f"❌ Sphinx error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🎙️  VocalXpert Voice Recognition Test")
    print("Make sure your microphone is working and not muted!")
    print("\nChoose test:")
    print("1. AssemblyAI API (online)")
    print("2. Sphinx Offline")
    print("3. Both")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        test_assemblyai()
    elif choice == "2":
        test_offline()
    elif choice == "3":
        test_assemblyai()
        test_offline()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()