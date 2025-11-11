import os
import logging
from typing import List, Optional
from ..app.schemas import Fine
from ..core.config import settings
from rag.retriever import RAGRetriever

try:
    import google.generativeai as genai
except ImportError:
    genai = None

class DefenseGenerator:
    """
    A class to handle the generation of AI-based defenses.
    """

    def __init__(self, fine_data: Fine):
        """
        Initialize with the structured fine data and the RAG retriever.
        """
        self.fine_data = fine_data
        self.retriever = RAGRetriever()
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini API if available
        if genai and settings.GOOGLE_AI_API_KEY:
            try:
                genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.gemini_available = True
                self.logger.info("Gemini API initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini API: {e}")
                self.gemini_available = False
        else:
            self.gemini_available = False
            self.logger.warning("Gemini API not available or API key not configured")

    def _sanitize_input(self, text: str) -> str:
        """
        Sanitizes input text to prevent prompt injection.
        Escapes double quotes and newlines.
        """
        return text.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')

    def generate_prompt(self) -> str:
        """
        Generates a detailed prompt for the AI based on the fine data
        and retrieved legal context.
        """
        self.logger.info("Generating prompt for AI defense...")
        
        # Create a query for the RAG retriever based on the fine data
        rag_query = (
            f"traffic fine in {self.fine_data.location} for infraction code "
            f"{self.fine_data.infraction_code} on {self.fine_data.date}"
        )
        
        # Retrieve relevant legal context
        try:
            retrieved_context = self.retriever.retrieve(rag_query)
            context_str = "\n\nRelevant Legal Context:\n" + "\n---\n".join(retrieved_context) if retrieved_context else ""
        except Exception as e:
            self.logger.warning(f"Failed to retrieve RAG context: {e}")
            context_str = ""

        prompt = (
            "Please act as a legal expert in Portuguese traffic law. "
            "Generate an administrative defense for the following traffic fine:\n\n"
            f"- Date: {self._sanitize_input(str(self.fine_data.date))}\n"
            f"- Location: {self._sanitize_input(self.fine_data.location)}\n"
            f"- Infraction Code: {self._sanitize_input(self.fine_data.infraction_code)}\n"
            f"- Fine Amount: {self._sanitize_input(str(self.fine_data.fine_amount))} EUR\n"
            f"- Infractor: {self._sanitize_input(self.fine_data.infractor)}\n"
            f"{context_str}\n\n"
            "The defense should be formal, well-structured, and reference relevant legislation if possible. "
            "Provide the best possible argument for contesting this fine. "
            "Write the response in Portuguese and format it as a formal administrative appeal letter."
        )
        return prompt

    def request_defense(self, prompt: str) -> str:
        """
        Generate defense using Gemini AI API or fallback to template.
        """
        self.logger.info("Requesting defense from AI...")
        
        if self.gemini_available:
            try:
                self.logger.debug("Calling Gemini API...")
                response = self.model.generate_content(prompt)
                
                if response and response.text:
                    generated_defense = response.text.strip()
                    self.logger.info("Successfully generated defense using AI")
                    return generated_defense
                else:
                    self.logger.warning("AI response was empty, falling back to template")
                    return self._get_template_defense()
                    
            except Exception as e:
                self.logger.error(f"AI generation failed: {e}")
                return self._get_template_defense()
        else:
            self.logger.info("Using template defense (AI not available)")
            return self._get_template_defense()
    
    def _get_template_defense(self) -> str:
        """
        Generate a template-based defense when AI is not available.
        This provides a structured response based on the fine data.
        """
        return f"""Exmo. Senhor Presidente da Autoridade Nacional de Segurança Rodoviária,

Eu, {self.fine_data.infractor}, venho por este meio apresentar a minha defesa administrativa em relação ao auto de contraordenação nº [NÚMERO DO AUTO], datado de {self.fine_data.date}, referente à infração verificada em {self.fine_data.location}.

**Factos:**
O auto refere-se a uma infração ao código da estrada, especificamente relacionada com o artigo {self.fine_data.infraction_code}, no valor de {self.fine_data.fine_amount} EUR.

**Argumentos de Defesa:**
1. **Questões de Procedimento:** Solicito que seja verificado se foram respeitados todos os procedimentos legais estabelecidos no Código da Estrada e no Regime Geral das Contraordenações.

2. **Necessidade de Esclarecimento:** Alguns elementos constantes no auto necessitam de esclarecimento adicional para uma análise completa dos factos.

3. **Circunstâncias Específicas:** As circunstâncias particulares do caso podem justificar uma revisão da aplicação da coima.

**Pedidos:**
- Revisão do montante da coima aplicada
- Esclarecimento dos fundamentos legais da infração
- Análise das circunstâncias específicas do caso

**Expectativa:**
Confio numa análise justa e equilibrada que considere todos os elementos relevantes do processo.

Com os melhores cumprimentos,
{self.fine_data.infractor}

[Data: {self.fine_data.date}]"""

    def active_learning_feedback(self, defense: str) -> str:
        """
        Placeholder for the active learning loop.
        Logs the defense generation for future improvement.
        """
        self.logger.info("Defense generation completed")
        self.logger.debug(f"Generated defense length: {len(defense)} characters")
        
        # In the future, this could collect user feedback to improve the AI prompts
        feedback = "auto_generated"  # Placeholder for future feedback system
        
        if feedback != "auto_generated":
            self.logger.info("Feedback received, will be used to improve future defenses.")
        
        return defense

    def generate(self) -> str:
        """
        Full pipeline for generating a defense.
        """
        prompt = self.generate_prompt()
        defense = self.request_defense(prompt)
        final_defense = self.active_learning_feedback(defense)
        return final_defense
