"""
Unit tests for the compliance agent
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import List, Dict, Any

from app.agents.compliance_agent import (
    ComplianceAgent,
    SpecializedAgentFactory,
    AgentOrchestrator
)
from app.agents.tools.document_tools import DocumentSearchTool
from app.agents.tools.search_tools import KnowledgeSearchTool
from app.agents.tools.analysis_tools import ComplianceAnalysisTool


class TestComplianceAgent:
    """Test cases for ComplianceAgent"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM"""
        llm = MagicMock()
        llm.ainvoke = AsyncMock()
        return llm
    
    @pytest.fixture
    def mock_tools(self):
        """Create mock tools"""
        tools = [
            MagicMock(name="document_search", description="Search documents"),
            MagicMock(name="compliance_analysis", description="Analyze compliance")
        ]
        return tools
    
    @pytest.fixture
    def agent(self, mock_llm, mock_tools):
        """Create agent instance"""
        with patch('app.agents.compliance_agent.create_openai_tools_agent'):
            with patch('app.agents.compliance_agent.AgentExecutor'):
                agent = ComplianceAgent(
                    llm=mock_llm,
                    tools=mock_tools,
                    verbose=False
                )
                return agent
    
    @pytest.mark.asyncio
    async def test_agent_run_simple(self, agent):
        """Test simple agent execution"""
        # Mock agent executor response
        agent.agent_executor.ainvoke = AsyncMock(return_value={
            "output": "Based on my analysis, you need to implement GDPR compliance measures.",
            "intermediate_steps": []
        })
        
        # Run agent
        result = await agent.run("What compliance measures do I need?")
        
        # Verify
        assert "GDPR compliance" in result["output"]
        assert result["tools_used"] == []
        agent.agent_executor.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_with_tools(self, agent):
        """Test agent execution with tool usage"""
        # Mock agent executor with tool usage
        from langchain.schema import AgentAction
        
        action = AgentAction(
            tool="document_search",
            tool_input={"query": "GDPR requirements"},
            log="Searching for GDPR requirements"
        )
        
        agent.agent_executor.ainvoke = AsyncMock(return_value={
            "output": "Found GDPR requirements in documents.",
            "intermediate_steps": [(action, "Document search results")]
        })
        
        # Run agent
        result = await agent.run("Find GDPR requirements")
        
        # Verify
        assert "GDPR requirements" in result["output"]
        assert "document_search" in result["tools_used"]
        assert len(result["intermediate_steps"]) == 1
    
    @pytest.mark.asyncio
    async def test_agent_with_chat_history(self, agent):
        """Test agent with conversation history"""
        # Mock agent executor
        agent.agent_executor.ainvoke = AsyncMock(return_value={
            "output": "Continuing from our previous discussion about GDPR...",
            "intermediate_steps": []
        })
        
        # Chat history
        chat_history = [
            {"role": "user", "content": "What is GDPR?"},
            {"role": "assistant", "content": "GDPR is the General Data Protection Regulation."}
        ]
        
        # Run with history
        result = await agent.run(
            "Tell me more about it",
            chat_history=chat_history
        )
        
        # Verify memory was updated
        assert agent.memory.chat_memory.messages
        assert "previous discussion" in result["output"]
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, agent):
        """Test agent error handling"""
        # Mock error
        agent.agent_executor.ainvoke = AsyncMock(
            side_effect=Exception("Agent execution failed")
        )
        
        # Test error is raised
        with pytest.raises(Exception) as exc_info:
            await agent.run("Test query")
        
        assert "Agent execution failed" in str(exc_info.value)
    
    def test_add_tool(self, agent):
        """Test adding a tool to agent"""
        initial_tool_count = len(agent.tools)
        
        # Add new tool
        new_tool = MagicMock(name="new_tool", description="New tool")
        agent.add_tool(new_tool)
        
        # Verify tool added
        assert len(agent.tools) == initial_tool_count + 1
        assert new_tool in agent.tools
    
    def test_remove_tool(self, agent):
        """Test removing a tool from agent"""
        # Add a tool first
        tool = MagicMock(name="test_tool", description="Test tool")
        agent.tools.append(tool)
        initial_count = len(agent.tools)
        
        # Remove tool
        agent.remove_tool("test_tool")
        
        # Verify tool removed
        assert len(agent.tools) == initial_count - 1
        assert tool not in agent.tools
    
    def test_clear_memory(self, agent):
        """Test clearing agent memory"""
        # Add some memory
        agent.memory.chat_memory.add_user_message("Test message")
        
        # Clear memory
        agent.clear_memory()
        
        # Verify memory cleared
        agent.memory.clear.assert_called_once()
    
    def test_get_available_tools(self, agent):
        """Test getting available tools"""
        tools = agent.get_available_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == len(agent.tools)
        
        for tool_info in tools:
            assert "name" in tool_info
            assert "description" in tool_info


class TestSpecializedAgentFactory:
    """Test cases for SpecializedAgentFactory"""
    
    def test_create_document_specialist(self):
        """Test creating document specialist agent"""
        with patch('app.agents.compliance_agent.ComplianceAgent') as MockAgent:
            agent = SpecializedAgentFactory.create_document_specialist()
            
            # Verify agent created with document tools
            MockAgent.assert_called_once()
            call_kwargs = MockAgent.call_args.kwargs
            assert "tools" in call_kwargs
            
            # Check tools are document-related
            tool_names = [t.name for t in call_kwargs["tools"]]
            assert "document_search" in tool_names
            assert "document_analysis" in tool_names
    
    def test_create_risk_analyst(self):
        """Test creating risk analyst agent"""
        with patch('app.agents.compliance_agent.ComplianceAgent') as MockAgent:
            agent = SpecializedAgentFactory.create_risk_analyst()
            
            # Verify agent created with risk tools
            MockAgent.assert_called_once()
            call_kwargs = MockAgent.call_args.kwargs
            assert "tools" in call_kwargs
            
            # Check tools are risk-related
            tool_names = [t.name for t in call_kwargs["tools"]]
            assert "risk_assessment" in tool_names
            assert "gap_analysis" in tool_names
    
    def test_create_research_agent(self):
        """Test creating research agent"""
        with patch('app.agents.compliance_agent.ComplianceAgent') as MockAgent:
            agent = SpecializedAgentFactory.create_research_agent()
            
            # Verify agent created with search tools
            MockAgent.assert_called_once()
            call_kwargs = MockAgent.call_args.kwargs
            assert "tools" in call_kwargs
            
            # Check tools are search-related
            tool_names = [t.name for t in call_kwargs["tools"]]
            assert "knowledge_search" in tool_names
            assert "web_search" in tool_names
    
    def test_create_compliance_auditor(self):
        """Test creating compliance auditor agent"""
        with patch('app.agents.compliance_agent.ComplianceAgent') as MockAgent:
            agent = SpecializedAgentFactory.create_compliance_auditor()
            
            # Verify agent created with audit tools
            MockAgent.assert_called_once()
            call_kwargs = MockAgent.call_args.kwargs
            assert "tools" in call_kwargs
            
            # Check tools are audit-related
            tool_names = [t.name for t in call_kwargs["tools"]]
            assert "compliance_analysis" in tool_names
            assert "checklist_generator" in tool_names


class TestAgentOrchestrator:
    """Test cases for AgentOrchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        with patch('app.agents.compliance_agent.SpecializedAgentFactory'):
            orchestrator = AgentOrchestrator()
            
            # Mock agents
            for name in orchestrator.agents:
                orchestrator.agents[name] = MagicMock()
                orchestrator.agents[name].run = AsyncMock(return_value={
                    "output": f"Response from {name} agent",
                    "tools_used": []
                })
            
            return orchestrator
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self, orchestrator):
        """Test sequential agent execution"""
        result = await orchestrator.execute_complex_task(
            "Analyze compliance",
            strategy="sequential"
        )
        
        # Verify all agents were called
        for name, agent in orchestrator.agents.items():
            agent.run.assert_called_once()
        
        # Verify results structure
        assert "combined_output" in result
        assert "agent_outputs" in result
        assert len(result["agent_outputs"]) == len(orchestrator.agents)
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self, orchestrator):
        """Test parallel agent execution"""
        result = await orchestrator.execute_complex_task(
            "Analyze compliance",
            strategy="parallel"
        )
        
        # Verify results from all agents
        assert len(result["agent_outputs"]) == len(orchestrator.agents)
        
        # Verify combined output
        assert result["combined_output"]
        for name in orchestrator.agents:
            assert f"Response from {name} agent" in result["combined_output"]
    
    @pytest.mark.asyncio
    async def test_hierarchical_execution(self, orchestrator):
        """Test hierarchical agent execution"""
        # Mock master agent
        orchestrator.master_agent = MagicMock()
        orchestrator.master_agent.run = AsyncMock(return_value={
            "output": "Master agent coordinated response",
            "tools_used": ["route_to_specialist"]
        })
        
        result = await orchestrator.execute_complex_task(
            "Complex compliance task",
            strategy="hierarchical"
        )
        
        # Verify master agent was used
        orchestrator.master_agent.run.assert_called_once()
        assert "master" in result["agent_outputs"]
    
    @pytest.mark.asyncio
    async def test_error_handling_in_orchestration(self, orchestrator):
        """Test error handling during orchestration"""
        # Make one agent fail
        orchestrator.agents["document"].run = AsyncMock(
            side_effect=Exception("Document agent failed")
        )
        
        # Execute with sequential strategy
        result = await orchestrator.execute_complex_task(
            "Test task",
            strategy="sequential"
        )
        
        # Verify error captured
        assert len(result["errors"]) == 1
        assert result["errors"][0]["agent"] == "document"
        assert "Document agent failed" in result["errors"][0]["error"]
    
    def test_synthesize_results(self, orchestrator):
        """Test result synthesis"""
        results = {
            "agent1": {
                "output": "Output 1",
                "tools_used": ["tool1", "tool2"]
            },
            "agent2": {
                "output": "Output 2",
                "tools_used": ["tool2", "tool3"]
            },
            "agent3": {
                "error": "Agent failed"
            }
        }
        
        synthesized = orchestrator._synthesize_results(results)
        
        # Verify synthesis
        assert "Output 1" in synthesized["combined_output"]
        assert "Output 2" in synthesized["combined_output"]
        assert len(synthesized["errors"]) == 1
        assert synthesized["errors"][0]["agent"] == "agent3"
        assert "tool1" in synthesized["tools_used"]
        assert "tool2" in synthesized["tools_used"]
        assert "tool3" in synthesized["tools_used"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])