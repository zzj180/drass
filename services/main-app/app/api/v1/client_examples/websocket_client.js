/**
 * WebSocket Client Example for Frontend Integration
 * This can be used in React components or any JavaScript frontend
 */

class ComplianceWebSocketClient {
    constructor(baseUrl = 'ws://localhost:8000', token = null) {
        this.baseUrl = baseUrl;
        this.token = token;
        this.ws = null;
        this.reconnectInterval = 5000;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.listeners = new Map();
        this.isConnected = false;
        this.messageQueue = [];
    }

    /**
     * Connect to WebSocket server
     */
    async connect() {
        return new Promise((resolve, reject) => {
            const wsUrl = this.token 
                ? `${this.baseUrl}/api/v1/ws?token=${this.token}`
                : `${this.baseUrl}/api/v1/ws`;

            try {
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    
                    // Send queued messages
                    this.flushMessageQueue();
                    
                    // Trigger connected event
                    this.emit('connected', { timestamp: new Date() });
                    
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event);
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.emit('error', error);
                };

                this.ws.onclose = (event) => {
                    console.log('WebSocket disconnected');
                    this.isConnected = false;
                    this.emit('disconnected', { code: event.code, reason: event.reason });
                    
                    // Attempt reconnection
                    this.reconnect();
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
    }

    /**
     * Reconnect to WebSocket server
     */
    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.emit('reconnect_failed', { attempts: this.reconnectAttempts });
            return;
        }

        this.reconnectAttempts++;
        console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);

        setTimeout(() => {
            this.connect().catch(error => {
                console.error('Reconnection failed:', error);
            });
        }, this.reconnectInterval);
    }

    /**
     * Send message to server
     */
    send(type, data = {}) {
        const message = {
            type,
            ...data,
            timestamp: new Date().toISOString()
        };

        if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            // Queue message if not connected
            this.messageQueue.push(message);
            console.log('Message queued (not connected):', message);
        }
    }

    /**
     * Send chat message
     */
    sendChatMessage(content, conversationId = null, stream = true) {
        this.send('chat', {
            content,
            conversation_id: conversationId,
            stream
        });
    }

    /**
     * Subscribe to a channel
     */
    subscribe(channel) {
        this.send('subscribe', { channel });
    }

    /**
     * Unsubscribe from a channel
     */
    unsubscribe(channel) {
        this.send('unsubscribe', { channel });
    }

    /**
     * Send ping to keep connection alive
     */
    ping() {
        this.send('ping');
    }

    /**
     * Handle incoming messages
     */
    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('Received message:', message);

            // Emit event based on message type
            this.emit(message.type, message);

            // Handle specific message types
            switch (message.type) {
                case 'pong':
                    // Ping response received
                    break;
                    
                case 'chat_response':
                    this.handleChatResponse(message);
                    break;
                    
                case 'stream_start':
                    this.handleStreamStart(message);
                    break;
                    
                case 'stream_chunk':
                    this.handleStreamChunk(message);
                    break;
                    
                case 'stream_end':
                    this.handleStreamEnd(message);
                    break;
                    
                case 'notification':
                    this.handleNotification(message);
                    break;
                    
                case 'error':
                    this.handleError(message);
                    break;
                    
                default:
                    // Unknown message type
                    console.warn('Unknown message type:', message.type);
            }
            
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }

    /**
     * Handle chat response
     */
    handleChatResponse(message) {
        console.log('Chat response:', message.content);
        // Update UI with chat response
    }

    /**
     * Handle stream start
     */
    handleStreamStart(message) {
        console.log('Stream started:', message.conversation_id);
        // Initialize streaming UI
    }

    /**
     * Handle stream chunk
     */
    handleStreamChunk(message) {
        console.log('Stream chunk:', message.content);
        // Append to streaming UI
    }

    /**
     * Handle stream end
     */
    handleStreamEnd(message) {
        console.log('Stream ended:', message.final_content);
        // Finalize streaming UI
    }

    /**
     * Handle notification
     */
    handleNotification(message) {
        console.log('Notification:', message.data);
        // Show notification in UI
    }

    /**
     * Handle error
     */
    handleError(message) {
        console.error('Server error:', message.message);
        // Show error in UI
    }

    /**
     * Register event listener
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * Remove event listener
     */
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * Emit event to listeners
     */
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Flush message queue
     */
    flushMessageQueue() {
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            this.ws.send(JSON.stringify(message));
        }
    }

    /**
     * Start heartbeat to keep connection alive
     */
    startHeartbeat(interval = 30000) {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.ping();
            }
        }, interval);
    }

    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
}

// React Hook Example
function useWebSocket(token) {
    const [client, setClient] = React.useState(null);
    const [isConnected, setIsConnected] = React.useState(false);
    const [messages, setMessages] = React.useState([]);

    React.useEffect(() => {
        const wsClient = new ComplianceWebSocketClient('ws://localhost:8000', token);
        
        // Setup event listeners
        wsClient.on('connected', () => {
            setIsConnected(true);
        });

        wsClient.on('disconnected', () => {
            setIsConnected(false);
        });

        wsClient.on('chat_response', (message) => {
            setMessages(prev => [...prev, message]);
        });

        wsClient.on('stream_chunk', (message) => {
            setMessages(prev => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage && lastMessage.conversation_id === message.conversation_id) {
                    lastMessage.content = message.accumulated;
                } else {
                    newMessages.push(message);
                }
                return newMessages;
            });
        });

        // Connect and start heartbeat
        wsClient.connect().then(() => {
            wsClient.startHeartbeat();
        });

        setClient(wsClient);

        // Cleanup
        return () => {
            wsClient.stopHeartbeat();
            wsClient.disconnect();
        };
    }, [token]);

    return {
        client,
        isConnected,
        messages,
        sendMessage: (content) => client?.sendChatMessage(content),
        subscribe: (channel) => client?.subscribe(channel),
        unsubscribe: (channel) => client?.unsubscribe(channel)
    };
}

// Vanilla JavaScript Example
async function example() {
    // Create client
    const client = new ComplianceWebSocketClient('ws://localhost:8000', 'your-auth-token');
    
    // Register event listeners
    client.on('connected', () => {
        console.log('Connected to server');
        
        // Subscribe to notifications
        client.subscribe('notifications');
    });
    
    client.on('chat_response', (message) => {
        console.log('Received chat response:', message);
        document.getElementById('chat-output').innerHTML += `<p>${message.content}</p>`;
    });
    
    client.on('stream_chunk', (message) => {
        // Update streaming output
        document.getElementById('stream-output').innerHTML = message.accumulated;
    });
    
    client.on('notification', (message) => {
        // Show notification
        alert('Notification: ' + JSON.stringify(message.data));
    });
    
    // Connect to server
    await client.connect();
    
    // Start heartbeat
    client.startHeartbeat();
    
    // Send chat message
    client.sendChatMessage('Hello, how can I ensure GDPR compliance?');
    
    // Clean up on page unload
    window.addEventListener('beforeunload', () => {
        client.disconnect();
    });
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ComplianceWebSocketClient;
}