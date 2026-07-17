import io
import logging
from PyPDF2 import PdfReader
from docx import Document

logger = logging.getLogger(__name__)

class DocumentParser:

    def extract_text(self, content: bytes, file_extension: str) -> str:
        try:
            if file_extension == '.txt':
                return self._extract_from_txt(content)
            elif file_extension == '.pdf':
                return self._extract_from_pdf(content)
            elif file_extension == '.docx':
                return self._extract_from_docx(content)
            else:
                raise ValueError(f"Unsupported file extension: {file_extension}")
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise Exception(f"Text extraction failed: {str(e)}")

    def _extract_from_txt(self, content: bytes) -> str:
        try:
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('latin-1')
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract text from TXT: {str(e)}")

    def _extract_from_pdf(self, content: bytes) -> str:
        try:
            pdf_reader = PdfReader(io.BytesIO(content))
            full_text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
            return full_text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    def _extract_from_docx(self, content: bytes) -> str:
        try:
            doc = Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs).strip()
        except Exception as e:
            raise Exception(f"Failed to extract text from DOCX: {str(e)}")
