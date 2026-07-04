import os
import logging
from groq import Groq
from rag_engine import build_context, build_context_with_sources

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

    async def process_query(self, query: str, category: str = "general") -> tuple:
        """Returns (answer, sources) tuple."""
        if not self.client:
            return self._mock_response(query, category), []
        try:
            context, sources = build_context_with_sources(query)
            user_message = query
            if context:
                user_message = f"Relevant legal context from Indian law documents:\n\n{context}\n\n---\n\nUser question: {query}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt(category)},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1024
            )
            answer = response.choices[0].message.content
            if not answer:
                raise Exception("Empty response from Groq API")
            return answer, sources

        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise Exception(f"AI processing error: {str(e)}")

    async def analyze_contract_risks(self, contract_text: str) -> dict:
        if not self.client:
            return {"error": "GROQ_API_KEY not configured"}
        try:
            if len(contract_text) > 4000:
                contract_text = contract_text[:4000] + "..."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": (
                        "You are a contract risk analyst specializing in Indian contract law. "
                        "Analyze the contract and respond in this exact JSON structure:\n"
                        "{\"summary\": \"one paragraph overview\", "
                        "\"risk_score\": <1-10>, "
                        "\"risks\": [{\"clause\": \"...\", \"risk\": \"...\", \"severity\": \"High|Medium|Low\"}], "
                        "\"missing_clauses\": [\"...\"], "
                        "\"recommendations\": [\"...\"]}"
                    )},
                    {"role": "user", "content": f"Analyze this contract for risks:\n\n{contract_text}"}
                ],
                max_tokens=1500
            )
            import json
            import re
            raw = response.choices[0].message.content.strip()
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"summary": raw, "risk_score": 0, "risks": [], "missing_clauses": [], "recommendations": []}
        except Exception as e:
            logger.error(f"Error analyzing contract: {str(e)}")
            raise Exception(f"Contract analysis error: {str(e)}")

    async def explain_document(self, document_text: str) -> str:
        if not self.client:
            return self._mock_document_explanation(document_text)
        try:
            if len(document_text) > 4000:
                document_text = document_text[:4000] + "..."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal and tax document expert. Summarize the document in simple language, identify key points and clauses, explain legal/tax terminology, highlight implications, and use bullet points for clarity."},
                    {"role": "user", "content": f"Please explain this document:\n\n{document_text}"}
                ],
                max_tokens=1024
            )
            answer = response.choices[0].message.content
            if not answer:
                raise Exception("Empty response from Groq API")
            return answer

        except Exception as e:
            logger.error(f"Error explaining document: {str(e)}")
            raise Exception(f"Document explanation error: {str(e)}")

    def _get_system_prompt(self, category: str) -> str:
        extras = {
            "legal": "Focus on Indian legal matters, IPC sections, Constitutional articles, and regulations.",
            "tax": "Focus on Indian tax laws, Income Tax Act sections, GST, deductions, and filing requirements.",
            "document": "Focus on explaining legal documents and contracts under Indian law."
        }
        base = "You are LexAssist, an AI legal and tax assistant specializing in Indian law. Provide clear simplified explanations, reference relevant Indian legal sections, and remind users this is not professional legal advice."
        return base + " " + extras.get(category, "")

    def generate_suggestions(self, query: str, category: str) -> list:
        if not self.client:
            return []
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You generate follow-up questions about Indian law."},
                    {"role": "user", "content": f"Based on this {category} question: \"{query}\"\n\nGenerate exactly 3 short follow-up questions. Return only the 3 questions as a plain numbered list, no explanations."}
                ],
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
        context, _ = build_context_with_sources(query)
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
