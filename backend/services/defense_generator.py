from ..app.schemas import Fine
from rag.retriever import RAGRetriever

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

    def generate_prompt(self) -> str:
        """
        Generates a detailed prompt for the Gemini CLI based on the fine data
        and retrieved legal context.
        """
        print("Generating prompt for AI defense...")
        
        # Create a query for the RAG retriever based on the fine data
        rag_query = (
            f"traffic fine in {self.fine_data.location} for infraction code "
            f"{self.fine_data.infraction_code} on {self.fine_data.date}"
        )
        
        # Retrieve relevant legal context
        retrieved_context = self.retriever.retrieve(rag_query)
        context_str = "\n\nRelevant Legal Context:\n" + "\n---\n".join(retrieved_context) if retrieved_context else ""

        prompt = (
            "Please act as a legal expert in Portuguese traffic law. "
            "Generate an administrative defense for the following traffic fine:\n\n"
            f"- Date: {self.fine_data.date}\n"
            f"- Location: {self.fine_data.location}\n"
            f"- Infraction Code: {self.fine_data.infraction_code}\n"
            f"- Fine Amount: {self.fine_data.fine_amount} EUR\n"
            f"- Infractor: {self.fine_data.infractor}\n"
            f"{context_str}\n\n"
            "The defense should be formal, well-structured, and reference relevant legislation if possible. "
            "Provide the best possible argument for contesting this fine."
        )
        return prompt

    def request_defense(self, prompt: str) -> str:
        """
        This function will interact with the Gemini CLI (me) to get the defense.
        This is a placeholder for the actual interaction logic.
        """
        print("Requesting defense from Gemini CLI...")
        # In a real implementation, this would involve calling the Gemini CLI
        # as a subprocess and capturing its output.
        print("--- GEMINI PROMPT ---")
        print(prompt)
        print("---------------------")
        
        # Placeholder response
        generated_defense = (
            "Exmo. Senhor Presidente da Autoridade Nacional de Segurança Rodoviária,\n\n"
            "Eu, [Nome do Infrator], venho por este meio apresentar a minha defesa em relação ao auto de contraordenação supracitado..."
            "\n\n[Argumento legal gerado pela AI]"
        )
        return generated_defense

    def active_learning_feedback(self, defense: str) -> str:
        """
        Placeholder for the active learning loop.
        Asks the user for feedback on the generated defense.
        """
        print("\n--- ACTIVE LEARNING FEEDBACK ---")
        print("Please review the generated defense:")
        print(defense)
        
        # In the CLI, we would ask for a rating or correction.
        feedback = "looks_good" # input("Rate the defense (good/bad/needs_edit): ")
        
        if feedback != "good":
            # If feedback is not good, we could ask for corrections
            # and use this to fine-tune the prompt or model in the future.
            print("Thank you for the feedback. This will be used to improve future defenses.")
        
        return defense # Return the defense, possibly after edits.

    def generate(self) -> str:
        """
        Full pipeline for generating a defense.
        """
        prompt = self.generate_prompt()
        defense = self.request_defense(prompt)
        final_defense = self.active_learning_feedback(defense)
        return final_defense
