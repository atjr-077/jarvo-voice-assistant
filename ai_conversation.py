"""
AI Conversation Module using Gemini API
Handles natural language conversations and intelligent responses
"""
import google.generativeai as genai
from typing import Optional, List, Dict
from config import get_gemini_api_key
import logging

logger = logging.getLogger(__name__)


class GeminiConversation:
    """Manages AI conversations with context and history"""
    
    def __init__(self, max_history: int = 10):
        """Initialize Gemini conversation handler"""
        # Suppress deprecation warnings
        import warnings
        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=UserWarning)

        self.api_key = get_gemini_api_key()
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 1.5 Flash for speed and intelligence
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.history: List[Dict[str, str]] = []
        self.max_history = max_history
        
    def ask(self, question: str) -> str:
        """Ask a question and get AI response"""
        try:
            # Build context from history
            context = self._build_context()
            
            # Richer system prompt
            system_instruction = (
                "You are Jarvo, an intelligent and helpful desktop voice assistant. "
                "Your goal is to help the user with their tasks, answer questions, and provide code or plans when asked. "
                "Keep your voice responses concise (1-3 sentences) but informative. "
                "If the user asks for a complex task (like planning or coding), you can be more detailed but summarize the main point first. "
                "Context of previous conversation:\n" + context
            )
            
            prompt = f"{system_instruction}\n\nUser: {question}"
            
            # Generate response
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            
            # Add to history
            self._add_to_history(question, answer)
            
            logger.info(f"AI Question: {question}")
            logger.info(f"AI Response: {answer}")
            
            return answer
            
        except Exception as e:
            logger.error(f"AI conversation error: {e}")
            return f"Sorry, I couldn't process that question right now."
    
    def _build_context(self) -> str:
        """Build conversation context from history"""
        if not self.history:
            return ""
        
        context_lines = []
        for turn in self.history[-self.max_history:]:
            context_lines.append(f"User: {turn['question']}")
            context_lines.append(f"Jarvo: {turn['answer']}")
        
        return "\n".join(context_lines)
    
    def _add_to_history(self, question: str, answer: str):
        """Add conversation turn to history"""
        self.history.append({
            'question': question,
            'answer': answer
        })
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def clear_history(self):
        """Clear conversation history"""
        self.history = []
        logger.info("Conversation history cleared")
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.history.copy()


# Global conversation instance
_conversation_instance: Optional[GeminiConversation] = None


def get_conversation() -> GeminiConversation:
    """Get or create global conversation instance"""
    global _conversation_instance
    if _conversation_instance is None:
        _conversation_instance = GeminiConversation()
    return _conversation_instance


def ask_ai(question: str) -> str:
    """Ask AI a question (convenience function)
    
    Args:
        question: User's question
        
    Returns:
        AI's response
    """
    try:
        conversation = get_conversation()
        return conversation.ask(question)
    except Exception as e:
        logger.error(f"Error in ask_ai: {e}")
        return "Sorry, I couldn't process that question. Please check your API key configuration."


def clear_conversation():
    """Clear conversation history (convenience function)"""
    try:
        conversation = get_conversation()
        conversation.clear_history()
    except Exception:
        pass


if __name__ == "__main__":
    # Test the AI conversation
    print("Testing Gemini AI Conversation...")
    
    try:
        conv = GeminiConversation()
        
        # Test questions
        questions = [
            "What is the capital of France?",
            "Tell me a fun fact about it",
            "What's 2+2?",
        ]
        
        for q in questions:
            print(f"\nQ: {q}")
            answer = conv.ask(q)
            print(f"A: {answer}")
            
    except Exception as e:
        print(f"Error: {e}")
