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
            
            # Calculate optimal timeout based on max_tokens
            from app.core.performance_config import performance_config
            optimal_timeout = performance_config.get_optimal_timeout(max_tokens or settings.LLM_MAX_TOKENS or 2048)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key or '123456'}",  # Use 123456 as default
                        "Content-Type": "application/json"
                    },
                    timeout=optimal_timeout  # Dynamic timeout based on token count
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Enhanced content cleaning and validation
                    import re
                    
                    # First, remove <think> tags and their content
                    think_pattern = r'<think>.*?</think>\s*'
                    content = re.sub(think_pattern, '', content, flags=re.DOTALL)
                    
                    # Remove standalone <think> tags that might not be closed
                    content = re.sub(r'<think>.*', '', content, flags=re.DOTALL)
                    
                    # Clean up any remaining malformed content
                    # Remove excessive numbers and repetitive patterns
                    content = re.sub(r'\d{10,}', '', content)  # Remove long number sequences
                    content = re.sub(r'(\d+\.){5,}', '', content)  # Remove repetitive number patterns
                    # Keep valid characters including markdown formatting
                    content = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()（）【】""''""''，。！？；：\n\r\*\#\-\+\=\|\[\]\(\)]', '', content)
                    
                    # Clean up excessive whitespace but preserve line breaks for formatting
                    content = re.sub(r'[ \t]+', ' ', content)  # Replace multiple spaces/tabs with single space
                    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Replace multiple line breaks with double line break
                    content = content.strip()
                    
                    # Validate content quality
                    def is_valid_content(text):
                        if not text or len(text.strip()) < 10:
                            return False
                        # Check for excessive repetition
                        words = text.split()
                        if len(words) > 10:
                            unique_words = set(words)
                            if len(unique_words) / len(words) < 0.3:  # Less than 30% unique words
                                return False
                        # Check for excessive numbers
                        if len(re.findall(r'\d', text)) / len(text) > 0.5:  # More than 50% numbers
                            return False
                        return True
                    
                    # If content is invalid, try to extract meaningful content
                    if not is_valid_content(content):
                        original_content = result["choices"][0]["message"]["content"]
                        
                        # Try to extract content before <think> tags
                        before_think = re.search(r'^([^<]*?)(?=<think>)', original_content, flags=re.DOTALL)
                        if before_think and is_valid_content(before_think.group(1)):
                            content = before_think.group(1).strip()
                        else:
                            # Try to extract content after </think> tags
                            after_think = re.search(r'</think>\s*(.+)', original_content, flags=re.DOTALL)
                            if after_think and is_valid_content(after_think.group(1)):
                                content = after_think.group(1).strip()
                            else:
                                # If all else fails, provide a helpful fallback
                                content = "抱歉，我无法生成有效的回复。请尝试重新表述您的问题，或者检查系统状态。"
                    
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