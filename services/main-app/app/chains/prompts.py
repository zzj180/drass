"""
Prompt templates for the compliance RAG chain
"""

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from app.chains.compliance_prompts import (
    DATA_COMPLIANCE_EXPERT_PROMPT,
    COMPLIANCE_QA_PROMPT_WITH_FILE,
    CompliancePromptConfig,
    DEFAULT_COMPLIANCE_CONFIG,
    get_compliance_prompt,
    format_file_context
)

# System prompt for compliance assistant - English version
COMPLIANCE_SYSTEM_PROMPT_EN = """You are an intelligent compliance assistant specialized in helping users understand and navigate regulatory requirements, compliance standards, and best practices. Your role is to provide accurate, helpful, and actionable compliance guidance based on the provided context.

Key responsibilities:
1. Provide accurate compliance information based on the context
2. Explain complex regulations in clear, understandable terms
3. Offer practical implementation guidance
4. Highlight important compliance risks and considerations
5. Suggest best practices and recommendations

Guidelines:
- Always base your answers on the provided context
- If information is not in the context, clearly state that
- Be precise and specific in your compliance guidance
- Highlight any critical compliance requirements or deadlines
- Provide step-by-step guidance when appropriate
- Use examples to illustrate complex concepts
- Maintain a professional and helpful tone

Remember: Compliance accuracy is critical. Only provide information you can verify from the context."""

# Use Chinese prompt as default
COMPLIANCE_SYSTEM_PROMPT = DATA_COMPLIANCE_EXPERT_PROMPT

# QA prompt template
COMPLIANCE_QA_PROMPT = """Answer the following question based on the provided context. If the answer is not in the context, please state that you don't have enough information to answer accurately.

Context:
{context}

Question: {input}

Please provide a comprehensive answer that:
1. Directly addresses the question
2. Includes relevant compliance details from the context
3. Highlights any important considerations or risks
4. Suggests next steps or recommendations if applicable

Answer:"""

# Condense question prompt for conversational retrieval
CONDENSE_QUESTION_PROMPT = """Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question that captures all relevant context from the conversation.

Chat History:
{chat_history}

Follow Up Question: {input}

Standalone Question:"""

# Multi-query prompt for query expansion
MULTI_QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are an AI assistant helping to improve document retrieval for compliance questions. 
Your task is to generate 3 different versions of the given question to help find relevant documents.

The different versions should:
1. Use synonyms and alternative phrasings
2. Be more specific or more general
3. Focus on different aspects of the question

Original question: {question}

Generate 3 alternative questions (one per line):"""
)

# Document summary prompt
DOCUMENT_SUMMARY_PROMPT = """Summarize the following document focusing on compliance-relevant information:

Document:
{document}

Provide a concise summary that highlights:
1. Key compliance requirements
2. Important deadlines or dates
3. Specific obligations or responsibilities
4. Relevant standards or regulations referenced

Summary:"""

# Compliance analysis prompt
COMPLIANCE_ANALYSIS_PROMPT = """Analyze the following information for compliance implications:

Information:
{content}

Provide an analysis covering:
1. Compliance requirements identified
2. Potential risks or gaps
3. Recommended actions
4. Priority level (High/Medium/Low)
5. Relevant stakeholders

Analysis:"""

# Answer refinement prompt
ANSWER_REFINEMENT_PROMPT = """Review and refine the following compliance answer for accuracy and completeness:

Original Answer:
{answer}

Context:
{context}

Please refine the answer to:
1. Ensure accuracy based on the context
2. Add any missing important details
3. Improve clarity and structure
4. Highlight critical compliance points
5. Add practical recommendations

Refined Answer:"""

# Fact extraction prompt
FACT_EXTRACTION_PROMPT = """Extract key compliance facts from the following text:

Text:
{text}

Extract and list:
1. Specific requirements
2. Deadlines or timeframes
3. Responsible parties
4. Standards or regulations referenced
5. Penalties or consequences
6. Exceptions or exemptions

Facts:"""

# Risk assessment prompt
RISK_ASSESSMENT_PROMPT = """Assess compliance risks based on the following information:

Information:
{information}

Provide a risk assessment including:
1. Identified compliance risks
2. Risk level (High/Medium/Low) for each
3. Potential impact
4. Likelihood of occurrence
5. Mitigation recommendations
6. Monitoring suggestions

Risk Assessment:"""

# Implementation guidance prompt
IMPLEMENTATION_GUIDANCE_PROMPT = """Provide implementation guidance for the following compliance requirement:

Requirement:
{requirement}

Context:
{context}

Provide guidance including:
1. Step-by-step implementation plan
2. Required resources
3. Timeline recommendations
4. Key stakeholders to involve
5. Common pitfalls to avoid
6. Success metrics
7. Documentation needs

Implementation Guide:"""

# Compliance checklist prompt
CHECKLIST_GENERATION_PROMPT = """Create a compliance checklist based on the following requirements:

Requirements:
{requirements}

Generate a checklist with:
1. Clear action items
2. Responsible parties for each item
3. Due dates or timeframes
4. Verification methods
5. Documentation requirements
6. Dependencies between items

Compliance Checklist:"""

# Regulatory update prompt
REGULATORY_UPDATE_PROMPT = """Analyze the following regulatory update for its implications:

Update:
{update}

Current State:
{current_state}

Analyze:
1. Key changes introduced
2. Impact on current compliance posture
3. Required actions
4. Implementation timeline
5. Affected processes or systems
6. Training needs

Analysis:"""

# Custom prompt creator
def create_custom_prompt(
    system_message: str,
    human_template: str,
    input_variables: list
) -> ChatPromptTemplate:
    """
    Create a custom prompt template
    
    Args:
        system_message: System message for the prompt
        human_template: Human message template
        input_variables: List of input variables
    
    Returns:
        ChatPromptTemplate instance
    """
    return ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", human_template)
    ])

# Prompt selector based on query type
class PromptSelector:
    """
    Select appropriate prompt based on query type
    """
    
    QUERY_TYPES = {
        "general": COMPLIANCE_QA_PROMPT,
        "analysis": COMPLIANCE_ANALYSIS_PROMPT,
        "risk": RISK_ASSESSMENT_PROMPT,
        "implementation": IMPLEMENTATION_GUIDANCE_PROMPT,
        "checklist": CHECKLIST_GENERATION_PROMPT,
        "update": REGULATORY_UPDATE_PROMPT
    }
    
    @classmethod
    def select_prompt(cls, query_type: str = "general") -> str:
        """
        Select prompt template based on query type
        
        Args:
            query_type: Type of query
        
        Returns:
            Appropriate prompt template
        """
        return cls.QUERY_TYPES.get(query_type, COMPLIANCE_QA_PROMPT)
    
    @classmethod
    def detect_query_type(cls, question: str) -> str:
        """
        Detect query type from question
        
        Args:
            question: User question
        
        Returns:
            Detected query type
        """
        question_lower = question.lower()
        
        # Risk-related keywords
        if any(word in question_lower for word in ["risk", "threat", "vulnerability", "exposure"]):
            return "risk"
        
        # Implementation keywords
        if any(word in question_lower for word in ["implement", "deploy", "setup", "configure", "how to"]):
            return "implementation"
        
        # Analysis keywords
        if any(word in question_lower for word in ["analyze", "assess", "evaluate", "review"]):
            return "analysis"
        
        # Checklist keywords
        if any(word in question_lower for word in ["checklist", "list", "steps", "tasks"]):
            return "checklist"
        
        # Update keywords
        if any(word in question_lower for word in ["update", "change", "new regulation", "amendment"]):
            return "update"
        
        return "general"