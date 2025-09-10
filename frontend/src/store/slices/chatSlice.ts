import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { chatService } from '@/services/chatService';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  metadata?: {
    model?: string;
    tokens?: number;
    sources?: Array<{
      title: string;
      url: string;
      snippet: string;
    }>;
  };
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  model?: string;
  systemPrompt?: string;
}

interface ChatState {
  conversations: Conversation[];
  activeConversation: Conversation | null;
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  streamingMessage: string;
}

const initialState: ChatState = {
  conversations: [],
  activeConversation: null,
  isLoading: false,
  isStreaming: false,
  error: null,
  streamingMessage: '',
};

export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ message, conversationId }: { message: string; conversationId?: string }) => {
    const response = await chatService.sendMessage(message, conversationId);
    return response;
  }
);

export const loadConversations = createAsyncThunk('chat/loadConversations', async () => {
  const conversations = await chatService.getConversations();
  return conversations;
});

export const loadConversation = createAsyncThunk(
  'chat/loadConversation',
  async (conversationId: string) => {
    const conversation = await chatService.getConversation(conversationId);
    return conversation;
  }
);

export const createConversation = createAsyncThunk(
  'chat/createConversation',
  async (title?: string) => {
    const conversation = await chatService.createConversation(title);
    return conversation;
  }
);

export const deleteConversation = createAsyncThunk(
  'chat/deleteConversation',
  async (conversationId: string) => {
    await chatService.deleteConversation(conversationId);
    return conversationId;
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setActiveConversation: (state, action: PayloadAction<Conversation | null>) => {
      state.activeConversation = action.payload;
    },
    addMessage: (state, action: PayloadAction<Message>) => {
      if (state.activeConversation) {
        state.activeConversation.messages.push(action.payload);
      }
    },
    updateStreamingMessage: (state, action: PayloadAction<string>) => {
      state.streamingMessage = action.payload;
    },
    setStreaming: (state, action: PayloadAction<boolean>) => {
      state.isStreaming = action.payload;
      if (!action.payload) {
        state.streamingMessage = '';
      }
    },
    clearError: (state) => {
      state.error = null;
    },
    updateConversationTitle: (state, action: PayloadAction<{ id: string; title: string }>) => {
      const conversation = state.conversations.find((c) => c.id === action.payload.id);
      if (conversation) {
        conversation.title = action.payload.title;
      }
      if (state.activeConversation?.id === action.payload.id) {
        state.activeConversation.title = action.payload.title;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.isStreaming = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isStreaming = false;
        if (state.activeConversation) {
          state.activeConversation.messages.push(action.payload);
        }
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isStreaming = false;
        state.error = action.error.message || 'Failed to send message';
      });

    builder
      .addCase(loadConversations.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(loadConversations.fulfilled, (state, action) => {
        state.isLoading = false;
        state.conversations = action.payload;
      })
      .addCase(loadConversations.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to load conversations';
      });

    builder
      .addCase(loadConversation.fulfilled, (state, action) => {
        state.activeConversation = action.payload;
      });

    builder
      .addCase(createConversation.fulfilled, (state, action) => {
        state.conversations.unshift(action.payload);
        state.activeConversation = action.payload;
      });

    builder
      .addCase(deleteConversation.fulfilled, (state, action) => {
        state.conversations = state.conversations.filter((c) => c.id !== action.payload);
        if (state.activeConversation?.id === action.payload) {
          state.activeConversation = null;
        }
      });
  },
});

export const {
  setActiveConversation,
  addMessage,
  updateStreamingMessage,
  setStreaming,
  clearError,
  updateConversationTitle,
} = chatSlice.actions;
export default chatSlice.reducer;