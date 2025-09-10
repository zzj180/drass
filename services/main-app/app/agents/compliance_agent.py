"""
LangChain Agent Implementation for Compliance Assistant
"""

from typing import List, Dict, Any, Optional, Union
from langchain.agents import AgentExecutor, create_openai_tools_agent, create_react_agent
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import Tool, StructuredTool
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.schema import AgentAction, AgentFinish
import logging
import json
from datetime import datetime

from app.core.config import settings
from app.agents.tools.document_tools import (
    DocumentSearchTool,
    DocumentAnalysisTool,
    DocumentExtractionTool
)
from app.agents.tools.search_tools import (
    KnowledgeSearchTool,
    WebSearchTool,
    SemanticSearchTool
)
from app.agents.tools.analysis_tools import (
    ComplianceAnalysisTool,
    RiskAssessmentTool,
    GapAnalysisTool,
    ChecklistGeneratorTool
)

logger = logging.getLogger(__name__)


class ComplianceAgent:
    """
    Main compliance agent with access to various tools
    """
    
    def __init__(
        self,
        llm: Optional[Any] = None,
        tools: Optional[List[Tool]] = None,
        memory: Optional[Any] = None,
        verbose: bool = False,
        max_iterations: int = 10,
        max_execution_time: float = 60.0
    ):
        """
        Initialize the compliance agent
        
        Args:
            llm: Language model instance
            tools: List of tools available to the agent
            memory: Memory instance for conversation history
            verbose: Whether to show agent reasoning
            max_iterations: Maximum number of agent iterations
            max_execution_time: Maximum execution time in seconds
        """
        self.llm = llm or self._create_default_llm()
        self.tools = tools or self._create_default_tools()
        self.memory = memory or self._create_default_memory()
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.max_execution_time = max_execution_time
        
        # Initialize agent
        self.agent = None
        self.agent_executor = None
        self._setup_agent()
    
    def _create_default_llm(self):
        """Create default LLM instance"""
        if settings.LLM_PROVIDER == "openrouter":
            return ChatOpenAI(
                model_name=settings.LLM_MODEL,
                openai_api_key=settings.OPENROUTER_API_KEY,
                openai_api_base=settings.OPENROUTER_BASE_URL,
                temperature=0.3,  # Lower temperature for more consistent agent behavior
                max_tokens=settings.LLM_MAX_TOKENS
            )
        else:
            return ChatOpenAI(
                model_name=settings.LLM_MODEL,
                openai_api_key=settings.LLM_API_KEY,
                temperature=0.3,
                max_tokens=settings.LLM_MAX_TOKENS
            )
    
    def _create_default_memory(self):
        """Create default memory instance"""
        return ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=2000,
            memory_key="chat_history",
            return_messages=True
        )
    
    def _create_default_tools(self) -> List[Tool]:
        """Create default tool set"""
        tools = []
        
        # Document tools
        tools.append(DocumentSearchTool().as_tool())
        tools.append(DocumentAnalysisTool().as_tool())
        tools.append(DocumentExtractionTool().as_tool())
        
        # Search tools
        tools.append(KnowledgeSearchTool().as_tool())
        tools.append(WebSearchTool().as_tool())
        tools.append(SemanticSearchTool().as_tool())
        
        # Analysis tools
        tools.append(ComplianceAnalysisTool().as_tool())
        tools.append(RiskAssessmentTool().as_tool())
        tools.append(GapAnalysisTool().as_tool())
        tools.append(ChecklistGeneratorTool().as_tool())
        
        return tools
    
    def _setup_agent(self):
        """Setup the agent and executor"""
        # Create agent prompt
        prompt = self._create_agent_prompt()
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=self.verbose,
            max_iterations=self.max_iterations,
            max_execution_time=self.max_execution_time,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )
    
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt template"""
        system_message = """You are a specialized compliance assistant agent with access to various tools to help users with compliance-related tasks.

Your capabilities include:
1. Searching and analyzing documents for compliance information
2. Performing compliance assessments and gap analysis
3. Generating risk assessments and compliance checklists
4. Searching knowledge bases and the web for regulatory information
5. Extracting and summarizing key compliance requirements

Guidelines for tool usage:
- Always use the most appropriate tool for the task
- Combine multiple tools when necessary for comprehensive answers
- Verify information accuracy when possible
- Provide specific, actionable recommendations
- Cite sources when referencing documents or regulations

When responding:
1. First understand what the user is asking for
2. Determine which tools are needed
3. Execute tools in logical sequence
4. Synthesize the results into a coherent response
5. Provide clear, structured answers with actionable insights

Remember: Accuracy is critical in compliance. Always verify important information and clearly indicate any uncertainties."""
        
        human_message = """{input}

{agent_scratchpad}"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", human_message)
        ])
        
        return prompt
    
    async def run(
        self,
        input_text: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        callbacks: Optional[List[AsyncCallbackHandler]] = None
    ) -> Dict[str, Any]:
        """
        Run the agent with given input
        
        Args:
            input_text: User input/question
            chat_history: Optional chat history
            callbacks: Optional callbacks for monitoring
        
        Returns:
            Agent response with output and intermediate steps
        """
        try:
            # Format chat history if provided
            if chat_history:
                for message in chat_history:
                    role = message.get("role", "")
                    content = message.get("content", "")
                    
                    if role == "user":
                        self.memory.chat_memory.add_user_message(content)
                    elif role == "assistant":
                        self.memory.chat_memory.add_ai_message(content)
            
            # Run agent
            result = await self.agent_executor.ainvoke(
                {"input": input_text},
                config={"callbacks": callbacks} if callbacks else None
            )
            
            # Format response
            return self._format_response(result)
            
        except Exception as e:
            logger.error(f"Agent execution error: {str(e)}", exc_info=True)
            raise
    
    def _format_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format agent response"""
        formatted = {
            "output": result.get("output", ""),
            "intermediate_steps": [],
            "tools_used": [],
            "execution_time": None
        }
        
        # Process intermediate steps
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if isinstance(step, tuple) and len(step) == 2:
                    action, observation = step
                    
                    if isinstance(action, AgentAction):
                        step_info = {
                            "tool": action.tool,
                            "tool_input": action.tool_input,
                            "observation": str(observation)[:500]  # Truncate long observations
                        }
                        formatted["intermediate_steps"].append(step_info)
                        
                        if action.tool not in formatted["tools_used"]:
                            formatted["tools_used"].append(action.tool)
        
        return formatted
    
    def add_tool(self, tool: Tool):
        """Add a new tool to the agent"""
        self.tools.append(tool)
        self._setup_agent()  # Reinitialize with new tool
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent"""
        self.tools = [t for t in self.tools if t.name != tool_name]
        self._setup_agent()  # Reinitialize without the tool
    
    def clear_memory(self):
        """Clear agent memory"""
        if self.memory:
            self.memory.clear()
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools with descriptions"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]


class SpecializedAgentFactory:
    """
    Factory for creating specialized agents with specific tool sets
    """
    
    @staticmethod
    def create_document_specialist() -> ComplianceAgent:
        """Create agent specialized in document processing"""
        tools = [
            DocumentSearchTool().as_tool(),
            DocumentAnalysisTool().as_tool(),
            DocumentExtractionTool().as_tool()
        ]
        
        return ComplianceAgent(
            tools=tools,
            verbose=False
        )
    
    @staticmethod
    def create_risk_analyst() -> ComplianceAgent:
        """Create agent specialized in risk analysis"""
        tools = [
            RiskAssessmentTool().as_tool(),
            GapAnalysisTool().as_tool(),
            ComplianceAnalysisTool().as_tool(),
            KnowledgeSearchTool().as_tool()
        ]
        
        return ComplianceAgent(
            tools=tools,
            verbose=False
        )
    
    @staticmethod
    def create_research_agent() -> ComplianceAgent:
        """Create agent specialized in research and information gathering"""
        tools = [
            KnowledgeSearchTool().as_tool(),
            WebSearchTool().as_tool(),
            SemanticSearchTool().as_tool(),
            DocumentSearchTool().as_tool()
        ]
        
        return ComplianceAgent(
            tools=tools,
            verbose=False
        )
    
    @staticmethod
    def create_compliance_auditor() -> ComplianceAgent:
        """Create agent specialized in compliance auditing"""
        tools = [
            ComplianceAnalysisTool().as_tool(),
            ChecklistGeneratorTool().as_tool(),
            GapAnalysisTool().as_tool(),
            DocumentAnalysisTool().as_tool(),
            RiskAssessmentTool().as_tool()
        ]
        
        return ComplianceAgent(
            tools=tools,
            verbose=False
        )


class AgentOrchestrator:
    """
    Orchestrate multiple specialized agents for complex tasks
    """
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.agents = {
            "document": SpecializedAgentFactory.create_document_specialist(),
            "risk": SpecializedAgentFactory.create_risk_analyst(),
            "research": SpecializedAgentFactory.create_research_agent(),
            "audit": SpecializedAgentFactory.create_compliance_auditor()
        }
        
        # Master agent for coordination
        self.master_agent = self._create_master_agent()
    
    def _create_master_agent(self) -> ComplianceAgent:
        """Create master coordination agent"""
        # Create routing tool
        routing_tool = Tool(
            name="route_to_specialist",
            description="Route task to appropriate specialist agent",
            func=self._route_to_specialist
        )
        
        return ComplianceAgent(
            tools=[routing_tool],
            verbose=True
        )
    
    async def _route_to_specialist(self, task: str, specialist: str) -> str:
        """Route task to specialist agent"""
        if specialist not in self.agents:
            return f"Unknown specialist: {specialist}"
        
        agent = self.agents[specialist]
        result = await agent.run(task)
        return result["output"]
    
    async def execute_complex_task(
        self,
        task: str,
        strategy: str = "sequential"
    ) -> Dict[str, Any]:
        """
        Execute complex task using multiple agents
        
        Args:
            task: Complex task description
            strategy: Execution strategy (sequential, parallel, hierarchical)
        
        Returns:
            Combined results from multiple agents
        """
        results = {}
        
        if strategy == "sequential":
            # Execute agents in sequence
            for name, agent in self.agents.items():
                try:
                    result = await agent.run(task)
                    results[name] = result
                except Exception as e:
                    logger.error(f"Agent {name} failed: {str(e)}")
                    results[name] = {"error": str(e)}
        
        elif strategy == "parallel":
            # Execute agents in parallel (simplified version)
            import asyncio
            
            tasks = []
            for name, agent in self.agents.items():
                tasks.append(agent.run(task))
            
            agent_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for name, result in zip(self.agents.keys(), agent_results):
                if isinstance(result, Exception):
                    results[name] = {"error": str(result)}
                else:
                    results[name] = result
        
        elif strategy == "hierarchical":
            # Use master agent to coordinate
            master_result = await self.master_agent.run(
                f"Coordinate the following task across specialists: {task}"
            )
            results["master"] = master_result
        
        return self._synthesize_results(results)
    
    def _synthesize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from multiple agents"""
        synthesized = {
            "combined_output": "",
            "agent_outputs": results,
            "tools_used": set(),
            "errors": []
        }
        
        # Combine outputs
        outputs = []
        for name, result in results.items():
            if isinstance(result, dict):
                if "error" in result:
                    synthesized["errors"].append({
                        "agent": name,
                        "error": result["error"]
                    })
                else:
                    outputs.append(result.get("output", ""))
                    
                    # Collect tools used
                    if "tools_used" in result:
                        synthesized["tools_used"].update(result["tools_used"])
        
        synthesized["combined_output"] = "\n\n".join(outputs)
        synthesized["tools_used"] = list(synthesized["tools_used"])
        
        return synthesized