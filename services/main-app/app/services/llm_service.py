"""
LLM service for managing language model interactions
"""

import logging
from typing import Optional, List, Dict, Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for managing LLM operations"""
    
    def __init__(self):
        self.llm = None
        self._initialized = False
        self.api_base = settings.LLM_BASE_URL or "http://localhost:8001/v1"
        self.api_key = settings.LLM_API_KEY or "not-required"
    
    async def initialize(self):
        """Initialize the LLM service"""
        if not self._initialized:
            logger.info(f"LLM service initialized with base URL: {self.api_base}")
            self._initialized = True
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate text from prompt using the Qwen model"""
        try:
            # 构建请求数据
            request_data = {
                "model": settings.LLM_MODEL or "vllm",  # Use vllm as default
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens or settings.LLM_MAX_TOKENS or 2048,
                "temperature": temperature or settings.LLM_TEMPERATURE or 0.7
            }
            
            # 记录发送给VLLM的请求内容
            logger.info(f"发送给VLLM的请求内容: {request_data}")
            logger.info(f"用户提示词: {prompt}")
            logger.info(f"Temperature: {temperature or settings.LLM_TEMPERATURE or 0.7}")
            logger.info(f"Max tokens: {max_tokens}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key or '123456'}",  # Use 123456 as default
                        "Content-Type": "application/json"
                    },
                    timeout=300.0  # Increase timeout to 300 seconds for large models
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Remove <think> tags and their content if present
                    import re
                    # Pattern to match <think>...</think> including newlines
                    think_pattern = r'<think>.*?</think>\s*'
                    content = re.sub(think_pattern, '', content, flags=re.DOTALL)
                    
                    # Also remove standalone <think> tags that might not be closed
                    content = re.sub(r'<think>.*', '', content, flags=re.DOTALL)
                    
                    # Trim any leading/trailing whitespace
                    content = content.strip()
                    
                    # If content is empty after removing think tags, try to extract some meaningful content
                    if not content:
                        # Try to get the original content and extract something useful
                        original_content = result["choices"][0]["message"]["content"]
                        
                        # Check if content is wrapped in <think> tags without proper closing
                        if original_content.startswith('<think>') and not original_content.endswith('</think>'):
                            # Extract content from within <think> tags and generate a response
                            think_content = re.search(r'<think>(.*)', original_content, flags=re.DOTALL)
                            if think_content:
                                think_text = think_content.group(1).strip()
                                # Use the thinking content to generate a more natural response
                                # Instead of fixed templates, try to extract the actual answer from thinking
                                if len(think_text) > 100:  # If there's substantial thinking content
                                    # Try to find the actual answer within the thinking
                                    # Look for patterns that indicate the actual response
                                    answer_patterns = [
                                        r'所以.*?回答.*?是[：:](.*)',
                                        r'因此.*?我的回答.*?是[：:](.*)',
                                        r'总结.*?[：:](.*)',
                                        r'结论.*?[：:](.*)',
                                        r'我的建议.*?[：:](.*)',
                                        r'基于.*?分析.*?[：:](.*)'
                                    ]
                                    
                                    for pattern in answer_patterns:
                                        match = re.search(pattern, think_text, flags=re.DOTALL)
                                        if match:
                                            content = match.group(1).strip()
                                            break
                                    
                                    # If no pattern matched, use the last part of thinking as response
                                    if not content:
                                        # Take the last 200 characters as potential response
                                        content = think_text[-200:].strip()
                                        # Clean up any incomplete sentences
                                        if content and not content.endswith(('.', '。', '!', '！', '?', '？')):
                                            content += "..."
                                else:
                                    # For short thinking content, generate a simple response
                                    content = "我理解您的问题，让我为您提供一些帮助。"
                            else:
                                content = "我理解您的问题，让我为您提供一些帮助。"
                        else:
                            # Look for any text after <think> tags
                            after_think = re.search(r'</think>\s*(.+)', original_content, flags=re.DOTALL)
                            if after_think:
                                content = after_think.group(1).strip()
                            else:
                                # If still empty, return a helpful message
                                content = "我理解您的问题，让我为您提供一些帮助。"
                    
                    return content
                else:
                    logger.error(f"LLM API error: {response.status_code} - {response.text}")
                    return f"Error: LLM service returned status {response.status_code}"
                    
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error generating response: {str(e)}\n{error_details}")
            # Return a user-friendly error message
            if "connection" in str(e).lower():
                return "Error: Unable to connect to LLM service. Please check if the service is running."
            elif "timeout" in str(e).lower():
                return "Error: LLM service request timed out. Please try again."
            else:
                return f"Error generating response: {str(e)}"
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get LLM service statistics"""
        return {
            "status": "operational",
            "model": settings.LLM_MODEL,
            "provider": settings.LLM_PROVIDER
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the LLM service"""
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "model": settings.LLM_MODEL,
            "provider": settings.LLM_PROVIDER
        }
    
    async def close(self):
        """Close the LLM service"""
        logger.info("Closing LLM service")
        self._initialized = False


# Singleton instance
llm_service = LLMService()