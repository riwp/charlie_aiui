import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types  # CRITICAL: Required for configuration compilation

# Setup logging to see what Gemini is doing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiHelper:
    def __init__(self):
        # Load the key from your specific secrets path
        load_dotenv('/home/mfsli1/aiui/secrets/.env')
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            logger.error("GEMINI_API_KEY not found in .env file!")
            raise ValueError("Missing Gemini API Key")

        # Initialize the persistent client
        self.client = genai.Client(api_key=api_key)
        # Using standard 2.5 flash or preview tag variant
        self.model_id = 'gemini-2.5-flash'

    def generate_insight(self, prompt, system_instruction=None):
        """
        Sends a prompt to Gemini and returns the text response.
        """
        try:
            logger.info("Sending request to Gemini...")
            
            # FIXED: Compile structural types configurations instead of standard python dict maps
            config = types.GenerateContentConfig()
            if system_instruction:
                config.system_instruction = system_instruction

            # Send payload directly out to generation gateway structures
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=config
            )

            if response and response.text:
                return response.text.strip()
            
            return "Error: Gemini returned an empty response."

        except Exception as e:
            logger.exception("Error during Gemini generation")
            return f"Error: {str(e)}"

# Create a singleton instance for the app to use
gemini_bot = GeminiHelper()