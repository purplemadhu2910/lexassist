import os
import logging
from groq import Groq
from rag_engine import build_context

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found. Using mock responses.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.1-8b-instant"

    async def process_query(self, query: str, category: str = "general") -> str:
        if not self.client:
            return self._mock_response(query, category)
        try:
            context = build_context(query)
            user_message = query
            if context:
                user_message = f"Relevant legal context from Indian law documents:\n\n{context}\n\n---\n\nUser question: {query}"

            prompt = self._get_system_prompt(category) + "\n\n" + user_message
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024
            )
            answer = response.choices[0].message.content
            if not answer:
                raise Exception("Empty response from Groq API")
            disclaimer = "\n\nDisclaimer: This is AI-generated information and not legal advice. Please consult a qualified professional for specific legal or tax matters."
            rag_note = "\n\nThis response was enhanced using Indian legal documents including IPC, Constitution, Income Tax Act, and CRPC." if context else ""
            return answer + rag_note + disclaimer

        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise Exception(f"AI processing error: {str(e)}")

    async def explain_document(self, document_text: str) -> str:
        if not self.client:
            return self._mock_document_explanation(document_text)
        try:
            if len(document_text) > 4000:
                document_text = document_text[:4000] + "..."

            prompt = """You are a legal and tax document expert. Your task is to:
1. Summarize the document in simple, easy-to-understand language
2. Identify key points and important clauses
3. Explain any legal or tax terminology
4. Highlight potential implications for the reader
5. Use bullet points for clarity

Please explain this document:

""" + document_text

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024
            )
            answer = response.choices[0].message.content
            if not answer:
                raise Exception("Empty response from Groq API")
            disclaimer = "\n\nDisclaimer: This is an AI-generated explanation and not legal advice. Consult a professional for specific guidance."
            return answer + disclaimer

        except Exception as e:
            logger.error(f"Error explaining document: {str(e)}")
            raise Exception(f"Document explanation error: {str(e)}")

    def _get_system_prompt(self, category: str) -> str:
        base = """You are LexAssist, an AI legal and tax assistant specializing in Indian law. Your role is to:
1. Provide clear, simplified explanations of legal and tax concepts
2. Always reference relevant Indian legal sections, acts, or statutes when applicable
3. Use easy-to-understand language
4. Be helpful but remind users this is not professional legal advice
5. When context from legal documents is provided, use it to give accurate, grounded answers"""

        extras = {
            "legal": "\n\nFocus on Indian legal matters, IPC sections, Constitutional articles, and regulations.",
            "tax": "\n\nFocus on Indian tax laws, Income Tax Act sections, GST, deductions, and filing requirements.",
            "document": "\n\nFocus on explaining legal documents and contracts under Indian law."
        }
        return base + extras.get(category, "")

    def generate_suggestions(self, query: str, category: str) -> list:
        if not self.client:
            return []
        try:
            prompt = f"""Based on this {category} question: "{query}"

Generate exactly 3 short follow-up questions a user might ask next about Indian {category} law.
Return only the 3 questions as a plain numbered list, no explanations."""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            raw = response.choices[0].message.content.strip()
            suggestions = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Strip leading numbering like "1." or "1)" or "-"
                cleaned = line.lstrip("0123456789.-) ").strip()
                if cleaned:
                    suggestions.append(cleaned)
            return suggestions[:3]
        except Exception:
            return []

    def _mock_response(self, query: str, category: str) -> str:
        context = build_context(query)
        context_note = "Relevant context was found in Indian legal documents." if context else "No matching legal documents were found for this query."
        return f"""Mock Response (GROQ_API_KEY not configured)

Your question: "{query}"
Category: {category}

{context_note}

To get real responses, add your GROQ_API_KEY to the .env file and restart the backend.

Disclaimer: This is AI-generated information and not legal advice."""

    def _mock_document_explanation(self, text: str) -> str:
        return f"""Mock Document Explanation (GROQ_API_KEY not configured)

Document contains {len(text.split())} words.

To get real explanations, add your GROQ_API_KEY to the .env file and restart the backend.

Disclaimer: This is an AI-generated explanation and not legal advice."""
