import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  Avatar,
  styled,
  useTheme,
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
} from '@mui/icons-material';
import { v4 as uuidv4 } from 'uuid';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const ChatContainer = styled(Box)(({ theme }) => ({
  height: '100vh',
  display: 'flex',
  flexDirection: 'column',
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
}));

const MessagesArea = styled(Box)(({ theme }) => ({
  flex: 1,
  overflowY: 'auto',
  padding: theme.spacing(2),
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(2),
}));

const MessageBubble = styled(Paper)<{ isuser: string }>(({ theme, isuser }) => ({
  padding: theme.spacing(2),
  maxWidth: '90%', // 增加最大宽度，支持更长的回答
  minWidth: '200px', // 设置最小宽度，确保显示效果
  alignSelf: isuser === 'true' ? 'flex-end' : 'flex-start',
  background: isuser === 'true' 
    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    : theme.palette.background.paper,
  color: isuser === 'true' ? 'white' : theme.palette.text.primary,
  borderRadius: isuser === 'true' ? '20px 20px 5px 20px' : '20px 20px 20px 5px',
  boxShadow: theme.shadows[3],
  wordWrap: 'break-word', // 支持长文本换行
  whiteSpace: 'pre-wrap', // 保持格式和换行
}));

const InputArea = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  background: 'rgba(255, 255, 255, 0.1)',
  backdropFilter: 'blur(10px)',
  display: 'flex',
  gap: theme.spacing(1),
  alignItems: 'center',
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  flex: 1,
  '& .MuiOutlinedInput-root': {
    background: 'rgba(255, 255, 255, 0.9)',
    borderRadius: '25px',
    '& fieldset': {
      border: 'none',
    },
    '&:hover fieldset': {
      border: 'none',
    },
    '&.Mui-focused fieldset': {
      border: `2px solid ${theme.palette.primary.main}`,
    },
  },
}));

const SendButton = styled(IconButton)(({ theme }) => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  width: 48,
  height: 48,
  '&:hover': {
    background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
  },
}));

const SimpleChatInterface: React.FC = () => {
  const theme = useTheme();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: uuidv4(),
      role: 'assistant',
      content: '欢迎使用磐石数据合规分析助手！我是您的数据合规分析专家，可以帮助您识别和解决数据合规风险。请告诉我您需要什么帮助？',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Create assistant message placeholder
    const assistantMessageId = uuidv4();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      const response = await fetch('http://localhost:8888/api/v1/test/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue,
          use_rag: false, // 暂时禁用RAG模式，提高响应速度
          temperature: 0.7, // 使用固定温度值，确保回答的专业性
          max_tokens: 2048, // 增加token数量，支持完整的长回答
        }),
        signal: AbortSignal.timeout(120000), // 增加超时时间到120秒，支持长回答生成
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('API Response:', data); // 添加调试日志
      
      let content = '抱歉，我无法生成回复。';
      if (data.status === 'success' && data.response) {
        content = data.response;
      } else if (data.message) {
        content = data.message;
      } else {
        console.error('Unexpected API response format:', data);
        content = '抱歉，我无法生成有效的回复。请检查LLM服务状态。';
      }

      // 模拟打字效果
      const words = content.split('');
      for (let i = 0; i <= words.length; i++) {
        const partialContent = words.slice(0, i).join('');
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantMessageId
              ? { ...msg, content: partialContent }
              : msg
          )
        );
        await new Promise(resolve => setTimeout(resolve, 20));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      let errorMessage = '抱歉，发送消息时出现错误。请检查网络连接或稍后重试。';
      
      if (error instanceof Error) {
        if (error.name === 'AbortError' || error.message.includes('timeout')) {
          errorMessage = '请求超时，请稍后重试。如果问题持续，请尝试简化您的问题。';
        } else if (error.message.includes('Failed to fetch')) {
          errorMessage = '网络连接失败，请检查网络连接或稍后重试。';
        } else if (error.message.includes('HTTP error')) {
          errorMessage = '服务器错误，请稍后重试。';
        }
      }
      
      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMessageId
            ? { 
                ...msg, 
                content: errorMessage
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading]);

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <ChatContainer>
      <MessagesArea>
        {messages.map((message) => (
          <Box key={message.id} sx={{ display: 'flex', alignItems: 'flex-end', gap: 1 }}>
            {message.role === 'assistant' && (
              <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                <BotIcon fontSize="small" />
              </Avatar>
            )}
            <MessageBubble isuser={message.role === 'user' ? 'true' : 'false'}>
              {message.role === 'assistant' ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                  components={{
                    h1: ({ children }) => (
                      <Typography variant="h5" sx={{ mb: 2, mt: 2, fontWeight: 'bold', color: 'inherit' }}>
                        {children}
                      </Typography>
                    ),
                    h2: ({ children }) => (
                      <Typography variant="h6" sx={{ mb: 1, mt: 2, fontWeight: 'bold', color: 'inherit' }}>
                        {children}
                      </Typography>
                    ),
                    h3: ({ children }) => (
                      <Typography variant="subtitle1" sx={{ mb: 1, mt: 1, fontWeight: 'bold', color: 'inherit' }}>
                        {children}
                      </Typography>
                    ),
                    p: ({ children }) => (
                      <Typography variant="body1" sx={{ mb: 1, lineHeight: 1.6, color: 'inherit' }}>
                        {children}
                      </Typography>
                    ),
                    ul: ({ children }) => (
                      <Box component="ul" sx={{ mb: 1, pl: 2, color: 'inherit' }}>
                        {children}
                      </Box>
                    ),
                    ol: ({ children }) => (
                      <Box component="ol" sx={{ mb: 1, pl: 2, color: 'inherit' }}>
                        {children}
                      </Box>
                    ),
                    li: ({ children }) => (
                      <Typography component="li" variant="body1" sx={{ mb: 0.5, color: 'inherit' }}>
                        {children}
                      </Typography>
                    ),
                    strong: ({ children }) => (
                      <Typography component="strong" sx={{ fontWeight: 'bold', color: 'inherit' }}>
                        {children}
                      </Typography>
                    ),
                    code: ({ children, className }) => {
                      const isInline = !className;
                      return isInline ? (
                        <code style={{ 
                          backgroundColor: 'rgba(0,0,0,0.1)', 
                          padding: '2px 4px', 
                          borderRadius: '3px',
                          fontFamily: 'monospace',
                          fontSize: '0.9em'
                        }}>
                          {children}
                        </code>
                      ) : (
                        <code className={className}>{children}</code>
                      );
                    },
                    blockquote: ({ children }) => (
                      <Box 
                        component="blockquote" 
                        sx={{ 
                          borderLeft: '4px solid rgba(0,0,0,0.2)', 
                          pl: 2, 
                          ml: 0, 
                          mb: 1,
                          fontStyle: 'italic',
                          color: 'inherit'
                        }}
                      >
                        {children}
                      </Box>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              ) : (
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {message.content}
                </Typography>
              )}
              <Typography 
                variant="caption" 
                sx={{ 
                  opacity: 0.7, 
                  mt: 1, 
                  display: 'block',
                  fontSize: '0.75rem'
                }}
              >
                {message.timestamp.toLocaleTimeString()}
              </Typography>
            </MessageBubble>
            {message.role === 'user' && (
              <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                <PersonIcon fontSize="small" />
              </Avatar>
            )}
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </MessagesArea>

      <InputArea>
        <StyledTextField
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="请输入您的数据合规相关问题..."
          multiline
          maxRows={4}
          disabled={isLoading}
        />
        <SendButton 
          onClick={handleSendMessage}
          disabled={isLoading || !inputValue.trim()}
        >
          <SendIcon />
        </SendButton>
      </InputArea>
    </ChatContainer>
  );
};

export default SimpleChatInterface;
