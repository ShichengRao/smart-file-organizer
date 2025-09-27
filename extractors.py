"""
File type detection and text extraction logic.
"""
import os
from pathlib import Path
from typing import Optional, Tuple
import logging

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

try:
    from pdfminer.high_level import extract_text as pdf_extract_text
except ImportError:
    pdf_extract_text = None

try:
    from docx import Document
except ImportError:
    Document = None

logger = logging.getLogger(__name__)


def detect_file_type(file_path: Path) -> str:
    """Detect file type based on extension."""
    suffix = file_path.suffix.lower()
    
    if suffix in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']:
        return 'image'
    elif suffix == '.pdf':
        return 'pdf'
    elif suffix in ['.docx', '.doc']:
        return 'docx'
    elif suffix == '.txt':
        return 'text'
    else:
        return 'unknown'


def extract_text_from_image(file_path: Path) -> Optional[str]:
    """Extract text from image using OCR."""
    if not pytesseract or not Image:
        logger.warning("OCR dependencies not available. Install pytesseract and pillow.")
        return None
    
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip() if text else None
    except Exception as e:
        logger.error(f"Error extracting text from image {file_path}: {e}")
        return None


def extract_text_from_pdf(file_path: Path) -> Optional[str]:
    """Extract text from PDF."""
    if not pdf_extract_text:
        logger.warning("PDF extraction dependencies not available. Install pdfminer.six.")
        return None
    
    try:
        text = pdf_extract_text(str(file_path))
        return text.strip() if text else None
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        return None


def extract_text_from_docx(file_path: Path) -> Optional[str]:
    """Extract text from Word document."""
    if not Document:
        logger.warning("DOCX extraction dependencies not available. Install python-docx.")
        return None
    
    try:
        doc = Document(file_path)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip() if text else None
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {file_path}: {e}")
        return None


def extract_text_from_txt(file_path: Path) -> Optional[str]:
    """Extract text from plain text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return text.strip() if text else None
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
        return None


def extract_text(file_path: Path) -> Tuple[str, Optional[str]]:
    """
    Extract text from a file based on its type.
    
    Returns:
        Tuple of (file_type, extracted_text)
    """
    file_type = detect_file_type(file_path)
    
    if file_type == 'image':
        text = extract_text_from_image(file_path)
    elif file_type == 'pdf':
        text = extract_text_from_pdf(file_path)
    elif file_type == 'docx':
        text = extract_text_from_docx(file_path)
    elif file_type == 'text':
        text = extract_text_from_txt(file_path)
    else:
        logger.warning(f"Unsupported file type: {file_type} for {file_path}")
        text = None
    
    return file_type, text