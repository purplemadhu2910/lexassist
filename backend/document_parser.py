import io
import logging

logger = logging.getLogger(__name__)

class DocumentParser:

    def extract_text(self, content: bytes, file_extension: str) -> str:
        try:
            if file_extension == '.txt':
                return self._extract_from_txt(content)
            elif file_extension == '.pdf':
                return self._extract_from_pdf(content)
            else:
                raise ValueError(f"Unsupported file extension: {file_extension}")

        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise Exception(f"Text extraction failed: {str(e)}")

    def _extract_from_txt(self, content: bytes) -> str:
        try:
            # Try reading as UTF-8 first, fall back to latin-1 if that fails
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('latin-1')
            return text.strip()

        except Exception as e:
            raise Exception(f"Failed to extract text from TXT: {str(e)}")

    def _extract_from_pdf(self, content: bytes) -> str:
        try:
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                raise Exception("PyPDF2 not installed. Run: pip install PyPDF2")

            pdf_file = io.BytesIO(content)
            pdf_reader = PdfReader(pdf_file)

            text_parts = []
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())

            full_text = "\n".join(text_parts)
            return full_text.strip()

        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
