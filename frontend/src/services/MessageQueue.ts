/**
 * Message Queue for managing WebSocket messages with priorities and batching
 */

export interface QueuedMessage {
  id: string;
  priority: 'high' | 'normal' | 'low';
  data: any;
  timestamp: number;
  retries: number;
  maxRetries: number;
}

export interface MessageQueueConfig {
  maxSize?: number;
  maxRetries?: number;
  batchSize?: number;
  flushInterval?: number;
}

export class MessageQueue {
  private queue: Map<string, QueuedMessage> = new Map();
  private priorityOrder: QueuedMessage[] = [];
  private config: Required<MessageQueueConfig>;
  private flushTimer: NodeJS.Timeout | null = null;
  private processing = false;
  private onFlush: ((messages: QueuedMessage[]) => Promise<void>) | null = null;

  constructor(config: MessageQueueConfig = {}) {
    this.config = {
      maxSize: config.maxSize ?? 1000,
      maxRetries: config.maxRetries ?? 3,
      batchSize: config.batchSize ?? 10,
      flushInterval: config.flushInterval ?? 100,
    };
  }

  /**
   * Add message to queue
   */
  enqueue(
    data: any,
    priority: 'high' | 'normal' | 'low' = 'normal',
    id?: string
  ): string {
    const messageId = id || this.generateId();
    
    const message: QueuedMessage = {
      id: messageId,
      priority,
      data,
      timestamp: Date.now(),
      retries: 0,
      maxRetries: this.config.maxRetries,
    };

    // Remove oldest messages if queue is full
    if (this.queue.size >= this.config.maxSize) {
      const oldestLowPriority = this.priorityOrder.find(m => m.priority === 'low');
      if (oldestLowPriority) {
        this.remove(oldestLowPriority.id);
      } else {
        const oldest = this.priorityOrder[0];
        if (oldest) {
          this.remove(oldest.id);
        }
      }
    }

    this.queue.set(messageId, message);
    this.updatePriorityOrder();
    this.scheduleFlush();

    return messageId;
  }

  /**
   * Remove message from queue
   */
  dequeue(id: string): QueuedMessage | undefined {
    const message = this.queue.get(id);
    if (message) {
      this.remove(id);
    }
    return message;
  }

  /**
   * Get next batch of messages to process
   */
  getBatch(size?: number): QueuedMessage[] {
    const batchSize = size || this.config.batchSize;
    return this.priorityOrder.slice(0, batchSize);
  }

  /**
   * Mark messages as processed
   */
  markProcessed(ids: string[]): void {
    ids.forEach(id => this.remove(id));
  }

  /**
   * Mark message as failed and retry if possible
   */
  markFailed(id: string, error?: Error): boolean {
    const message = this.queue.get(id);
    if (!message) {
      return false;
    }

    message.retries++;
    
    if (message.retries >= message.maxRetries) {
      console.error(`[MessageQueue] Message ${id} failed after ${message.retries} retries:`, error);
      this.remove(id);
      return false;
    }

    // Re-queue with lower priority
    if (message.priority === 'high') {
      message.priority = 'normal';
    } else if (message.priority === 'normal') {
      message.priority = 'low';
    }

    this.updatePriorityOrder();
    this.scheduleFlush();
    
    return true;
  }

  /**
   * Set flush handler
   */
  setFlushHandler(handler: (messages: QueuedMessage[]) => Promise<void>): void {
    this.onFlush = handler;
  }

  /**
   * Manually trigger flush
   */
  async flush(): Promise<void> {
    if (this.processing || this.queue.size === 0 || !this.onFlush) {
      return;
    }

    this.processing = true;
    
    try {
      const batch = this.getBatch();
      if (batch.length > 0) {
        await this.onFlush(batch);
        this.markProcessed(batch.map(m => m.id));
      }
    } catch (error) {
      console.error('[MessageQueue] Flush error:', error);
      // Messages remain in queue for retry
    } finally {
      this.processing = false;
      
      // Schedule next flush if queue not empty
      if (this.queue.size > 0) {
        this.scheduleFlush();
      }
    }
  }

  /**
   * Clear all messages
   */
  clear(): void {
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }
    
    this.queue.clear();
    this.priorityOrder = [];
    this.processing = false;
  }

  /**
   * Get queue size
   */
  size(): number {
    return this.queue.size;
  }

  /**
   * Get all messages
   */
  getAll(): QueuedMessage[] {
    return [...this.priorityOrder];
  }

  /**
   * Get messages by priority
   */
  getByPriority(priority: 'high' | 'normal' | 'low'): QueuedMessage[] {
    return this.priorityOrder.filter(m => m.priority === priority);
  }

  // Private methods

  private remove(id: string): void {
    this.queue.delete(id);
    this.priorityOrder = this.priorityOrder.filter(m => m.id !== id);
  }

  private updatePriorityOrder(): void {
    this.priorityOrder = Array.from(this.queue.values()).sort((a, b) => {
      // Sort by priority first
      const priorityWeight = { high: 3, normal: 2, low: 1 };
      const priorityDiff = priorityWeight[b.priority] - priorityWeight[a.priority];
      if (priorityDiff !== 0) {
        return priorityDiff;
      }
      
      // Then by timestamp (FIFO within same priority)
      return a.timestamp - b.timestamp;
    });
  }

  private scheduleFlush(): void {
    if (this.flushTimer || this.processing) {
      return;
    }

    this.flushTimer = setTimeout(() => {
      this.flushTimer = null;
      this.flush().catch(error => {
        console.error('[MessageQueue] Auto-flush error:', error);
      });
    }, this.config.flushInterval);
  }

  private generateId(): string {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get queue statistics
   */
  getStats(): {
    total: number;
    high: number;
    normal: number;
    low: number;
    processing: boolean;
    oldestMessage: number | null;
  } {
    const now = Date.now();
    const oldest = this.priorityOrder[0];
    
    return {
      total: this.queue.size,
      high: this.getByPriority('high').length,
      normal: this.getByPriority('normal').length,
      low: this.getByPriority('low').length,
      processing: this.processing,
      oldestMessage: oldest ? now - oldest.timestamp : null,
    };
  }
}

export default MessageQueue;