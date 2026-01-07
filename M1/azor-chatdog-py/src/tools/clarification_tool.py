"""
Clarification tool for AZØR chatdog.
Allows the LLM to request additional information from the user when questions are ambiguous.
"""

from google.genai.types import (
    Tool,
    FunctionDeclaration,
    Schema,
)


def ask_user_for_clarification(clarification_question: str, reason: str = None) -> str:
    """
    This function is called by the LLM when it needs clarification from the user.
    It pauses the conversation flow and prompts the user for additional information.
    
    :param clarification_question: The specific question to ask the user
    :param reason: Optional explanation of why clarification is needed
    :return: User's clarification response (to be provided by the execution loop)
    """
    # This function signature is for documentation purposes.
    # The actual implementation happens in the tool execution loop in ChatSession.
    # This will be called from chat_session.py when the LLM requests clarification.
    pass


def create_clarification_tool() -> Tool:
    """
    Creates the clarification tool definition for Gemini function calling.
    
    The LLM can call this tool when:
    - The user's question is ambiguous or vague
    - Important context is missing
    - Multiple interpretations are possible
    - Specific details are needed to provide an accurate answer
    
    :return: Tool object containing the clarification function declaration
    """
    clarification_declaration = FunctionDeclaration(
        name='ask_user_for_clarification',
        description=(
            'Request additional information from the user when their question is ambiguous, '
            'vague, or lacks necessary details. Use this tool when you need specific '
            'information to provide an accurate and helpful answer. The user will be '
            'prompted to provide the clarification, and you will receive their response '
            'to continue with the conversation.'
        ),
        parameters=Schema(
            type='object',
            properties={
                'clarification_question': Schema(
                    type='string',
                    description=(
                        'The specific, clear question to ask the user. '
                        'Make it focused and easy to understand. '
                        'Example: "Are you asking about Python 2 or Python 3?" '
                        'or "Which operating system are you using?"'
                    )
                ),
                'reason': Schema(
                    type='string',
                    description=(
                        'Optional brief explanation of why this clarification is needed. '
                        'Example: "The answer differs significantly between Python versions" '
                        'or "This feature behaves differently on Windows vs Linux"'
                    )
                )
            },
            required=['clarification_question']
        )
    )
    
    return Tool(function_declarations=[clarification_declaration])
