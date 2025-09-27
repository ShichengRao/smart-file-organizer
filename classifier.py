"""
LLM prompt and JSON parsing for categorization and renaming.
"""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


class FileClassifier:
    """Handles file classification using LLM."""
    
    def __init__(self, api_key: str):
        if not OpenAI:
            raise ImportError("OpenAI package not available. Install with: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
    
    def classify_file(self, filename: str, extracted_text: str) -> Optional[Dict[str, str]]:
        """
        Classify a file and suggest a new name based on its content.
        
        Args:
            filename: Original filename
            extracted_text: Text extracted from the file
            
        Returns:
            Dictionary with 'category' and 'new_filename' keys, or None if classification fails
        """
        if not extracted_text or not extracted_text.strip():
            logger.warning(f"No text content to classify for {filename}")
            return None
        
        prompt = self._build_prompt(filename, extracted_text)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a file organizer assistant. Analyze documents and provide structured categorization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None
    
    def _build_prompt(self, filename: str, text: str) -> str:
        """Build the classification prompt."""
        # Truncate text if too long
        max_text_length = 2000
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."
        
        return f"""
Analyze this document and provide categorization information.

Original filename: {filename}
Document content:
{text}

Please respond with a JSON object containing:
1. "category": A descriptive category name (e.g., "Uber Receipts", "Apple Payment Confirmations", "Travel Tickets", "Bank Statements", "Medical Records")
2. "new_filename": A descriptive filename including vendor/company, document type, and date if available (without file extension)

Guidelines:
- Keep category names consistent and descriptive
- Include dates in YYYY-MM-DD format when possible
- Include vendor/company name when identifiable
- Keep filenames under 100 characters
- Use underscores instead of spaces in filenames

Example response:
{{"category": "Uber Receipts", "new_filename": "uber_ride_receipt_2024-01-15_downtown"}}

Response:"""
    
    def _parse_response(self, response_content: str) -> Optional[Dict[str, str]]:
        """Parse the LLM response and extract category and filename."""
        try:
            # Try to find JSON in the response
            response_content = response_content.strip()
            
            # Look for JSON block
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.error("No JSON found in response")
                return None
            
            json_str = response_content[start_idx:end_idx]
            result = json.loads(json_str)
            
            # Validate required fields
            if 'category' not in result or 'new_filename' not in result:
                logger.error("Missing required fields in response")
                return None
            
            # Clean up the values
            result['category'] = self._clean_category(result['category'])
            result['new_filename'] = self._clean_filename(result['new_filename'])
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return None
    
    def _clean_category(self, category: str) -> str:
        """Clean and standardize category name."""
        # Remove extra whitespace and limit length
        category = category.strip()[:50]
        # Replace problematic characters for folder names
        category = category.replace('/', '_').replace('\\', '_')
        return category
    
    def _clean_filename(self, filename: str) -> str:
        """Clean and standardize filename."""
        # Remove extra whitespace and limit length
        filename = filename.strip()[:80]
        # Replace spaces with underscores and remove problematic characters
        filename = filename.replace(' ', '_')
        # Remove or replace problematic characters
        problematic_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in problematic_chars:
            filename = filename.replace(char, '_')
        # Remove multiple consecutive underscores
        while '__' in filename:
            filename = filename.replace('__', '_')
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        return filename