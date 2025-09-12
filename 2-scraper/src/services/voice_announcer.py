"""
Voice announcement service for the Employee Data Scraper.

This module provides text-to-speech functionality to announce pipeline completion
with a sexy male voice as requested.
"""

import logging
import time
from typing import Optional
import threading

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class VoiceAnnouncer:
    """
    Voice announcer service that provides text-to-speech functionality.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engine = None
        self.start_time = None
        
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                self._configure_voice()
                self.logger.info("Voice announcer initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize voice engine: {e}")
                self.engine = None
        else:
            self.logger.warning("pyttsx3 not available. Voice announcements will be disabled.")
    
    def _configure_voice(self):
        """Configure the voice engine for a sexy male voice."""
        if not self.engine:
            return
            
        try:
            # Get available voices
            voices = self.engine.getProperty('voices')
            
            # Look for male voices (preferably deep/attractive ones)
            male_voice = None
            for voice in voices:
                # Check if it's a male voice (common indicators)
                voice_name = voice.name.lower()
                voice_id = voice.id.lower()
                
                # Look for male voice indicators
                if any(indicator in voice_name or indicator in voice_id for indicator in 
                      ['male', 'man', 'david', 'alex', 'daniel', 'james', 'john', 'michael', 'richard']):
                    male_voice = voice
                    break
            
            if male_voice:
                self.engine.setProperty('voice', male_voice.id)
                self.logger.info(f"Using male voice: {male_voice.name}")
            else:
                # Fallback to first available voice
                if voices:
                    self.engine.setProperty('voice', voices[0].id)
                    self.logger.info(f"Using fallback voice: {voices[0].name}")
            
            # Configure voice properties for a sexy, deep male voice
            self.engine.setProperty('rate', 150)    # Slightly slower for more impact
            self.engine.setProperty('volume', 0.9)  # High volume
            
        except Exception as e:
            self.logger.error(f"Error configuring voice: {e}")
    
    def start_timing(self):
        """Start timing the pipeline execution."""
        self.start_time = time.time()
        self.logger.info("Pipeline timing started")
    
    def announce_completion(self, employee_count: int, additional_info: str = ""):
        """
        Announce pipeline completion with a sexy male voice.
        
        Args:
            employee_count: Number of employees successfully scraped
            additional_info: Additional information to include in the announcement
        """
        if not self.engine:
            self.logger.warning("Voice engine not available. Skipping voice announcement.")
            return
        
        # Calculate execution time
        if self.start_time:
            elapsed_minutes = (time.time() - self.start_time) / 60
            time_text = f"{elapsed_minutes:.1f} mins"
        else:
            time_text = "unknown time"
        
        # Create the announcement message
        message = f"Employee Data Fetching Complete, it took {time_text} and got {employee_count} valid Ennead Architects employee data. Oh Yeah!"
        
        if additional_info:
            message += f" {additional_info}"
        
        self.logger.info(f"Voice announcement: {message}")
        
        # Speak the message in a separate thread to avoid blocking
        def speak():
            try:
                self.engine.say(message)
                self.engine.runAndWait()
                self.logger.info("Voice announcement completed")
            except Exception as e:
                self.logger.error(f"Error during voice announcement: {e}")
        
        # Run in a separate thread
        thread = threading.Thread(target=speak, daemon=True)
        thread.start()
    
    def announce_error(self, error_message: str):
        """
        Announce an error with voice.
        
        Args:
            error_message: Error message to announce
        """
        if not self.engine:
            return
            
        message = f"Employee Data Fetching failed. {error_message}"
        
        def speak():
            try:
                self.engine.say(message)
                self.engine.runAndWait()
            except Exception as e:
                self.logger.error(f"Error during error announcement: {e}")
        
        thread = threading.Thread(target=speak, daemon=True)
        thread.start()
    
    def cleanup(self):
        """Clean up the voice engine resources."""
        if self.engine:
            try:
                self.engine.stop()
                self.logger.info("Voice engine cleaned up")
            except Exception as e:
                self.logger.error(f"Error cleaning up voice engine: {e}")


# Global voice announcer instance
voice_announcer = VoiceAnnouncer()
