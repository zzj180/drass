"""
Batch processor for optimized embedding generation
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import time
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """Batch request container"""
    texts: List[str]
    request_id: str
    timestamp: float
    future: asyncio.Future


class BatchProcessor:
    """Optimized batch processor for embeddings"""
    
    def __init__(
        self,
        batch_size: int = 32,
        max_wait_time: float = 0.1,
        max_queue_size: int = 1000
    ):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time  # Maximum wait time in seconds
        self.max_queue_size = max_queue_size
        
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.pending_requests = []
        self.processing = False
        self.processor_task = None
        
        # Statistics
        self.total_batches = 0
        self.total_texts = 0
        self.average_batch_size = 0
        self.average_wait_time = 0
        
    async def start(self):
        """Start the batch processor"""
        if not self.processing:
            self.processing = True
            self.processor_task = asyncio.create_task(self._process_batches())
            logger.info(f"Batch processor started (batch_size={self.batch_size}, max_wait={self.max_wait_time}s)")
    
    async def stop(self):
        """Stop the batch processor"""
        self.processing = False
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Batch processor stopped")
    
    async def add_request(
        self,
        texts: List[str],
        request_id: str
    ) -> asyncio.Future:
        """Add texts to processing queue"""
        future = asyncio.Future()
        request = BatchRequest(
            texts=texts,
            request_id=request_id,
            timestamp=time.time(),
            future=future
        )
        
        await self.queue.put(request)
        return future
    
    async def _process_batches(self):
        """Main batch processing loop"""
        while self.processing:
            try:
                await self._collect_and_process_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                await asyncio.sleep(0.1)
    
    async def _collect_and_process_batch(self):
        """Collect requests into batch and process"""
        batch_texts = []
        batch_requests = []
        batch_start_time = time.time()
        
        # Collect requests up to batch size or max wait time
        while len(batch_texts) < self.batch_size:
            try:
                remaining_time = self.max_wait_time - (time.time() - batch_start_time)
                
                if remaining_time <= 0 and batch_texts:
                    # Max wait time reached, process what we have
                    break
                
                timeout = min(remaining_time, 0.01) if batch_texts else None
                
                request = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=timeout
                )
                
                batch_requests.append(request)
                batch_texts.extend(request.texts)
                
            except asyncio.TimeoutError:
                if batch_texts:
                    # We have texts to process
                    break
                continue
        
        if batch_texts:
            await self._process_batch(batch_texts, batch_requests)
    
    async def _process_batch(
        self,
        texts: List[str],
        requests: List[BatchRequest]
    ):
        """Process a batch of texts"""
        try:
            # Import here to avoid circular dependency
            from app import embedding_model
            
            # Calculate wait times
            current_time = time.time()
            wait_times = [current_time - req.timestamp for req in requests]
            
            # Process embeddings
            logger.debug(f"Processing batch of {len(texts)} texts from {len(requests)} requests")
            result = await embedding_model.embed_texts(texts)
            embeddings = result["embeddings"]
            
            # Distribute results back to requests
            offset = 0
            for request in requests:
                request_embeddings = embeddings[offset:offset + len(request.texts)]
                offset += len(request.texts)
                
                # Set result in future
                request.future.set_result({
                    "embeddings": request_embeddings,
                    "model": result["model"],
                    "usage": {
                        **result["usage"],
                        "batch_size": len(texts),
                        "wait_time": current_time - request.timestamp
                    }
                })
            
            # Update statistics
            self._update_stats(len(texts), wait_times)
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Set exception for all requests
            for request in requests:
                if not request.future.done():
                    request.future.set_exception(e)
    
    def _update_stats(self, batch_size: int, wait_times: List[float]):
        """Update processing statistics"""
        self.total_batches += 1
        self.total_texts += batch_size
        
        # Update moving averages
        alpha = 0.1  # Smoothing factor
        self.average_batch_size = (
            alpha * batch_size + 
            (1 - alpha) * self.average_batch_size
        ) if self.average_batch_size > 0 else batch_size
        
        avg_wait = np.mean(wait_times)
        self.average_wait_time = (
            alpha * avg_wait + 
            (1 - alpha) * self.average_wait_time
        ) if self.average_wait_time > 0 else avg_wait
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            "batch_size_config": self.batch_size,
            "max_wait_time": self.max_wait_time,
            "queue_size": self.queue.qsize(),
            "total_batches": self.total_batches,
            "total_texts": self.total_texts,
            "average_batch_size": round(self.average_batch_size, 2),
            "average_wait_time": round(self.average_wait_time, 4),
            "processing": self.processing
        }


class DynamicBatchProcessor(BatchProcessor):
    """Dynamic batch processor with adaptive batch sizing"""
    
    def __init__(
        self,
        min_batch_size: int = 8,
        max_batch_size: int = 64,
        target_latency: float = 0.5
    ):
        super().__init__(batch_size=min_batch_size)
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.target_latency = target_latency
        
        # Adaptive parameters
        self.current_batch_size = min_batch_size
        self.latency_history = []
        self.adjustment_interval = 10  # Adjust every N batches
        
    async def _process_batch(
        self,
        texts: List[str],
        requests: List[BatchRequest]
    ):
        """Process batch with latency tracking"""
        start_time = time.time()
        await super()._process_batch(texts, requests)
        latency = time.time() - start_time
        
        # Track latency
        self.latency_history.append(latency)
        
        # Adjust batch size periodically
        if len(self.latency_history) >= self.adjustment_interval:
            self._adjust_batch_size()
            self.latency_history = []
    
    def _adjust_batch_size(self):
        """Dynamically adjust batch size based on latency"""
        avg_latency = np.mean(self.latency_history)
        
        if avg_latency > self.target_latency * 1.2:
            # Latency too high, reduce batch size
            self.current_batch_size = max(
                self.min_batch_size,
                int(self.current_batch_size * 0.8)
            )
            logger.info(f"Reduced batch size to {self.current_batch_size} (latency: {avg_latency:.3f}s)")
            
        elif avg_latency < self.target_latency * 0.8:
            # Latency low, increase batch size
            self.current_batch_size = min(
                self.max_batch_size,
                int(self.current_batch_size * 1.2)
            )
            logger.info(f"Increased batch size to {self.current_batch_size} (latency: {avg_latency:.3f}s)")
        
        self.batch_size = self.current_batch_size


def create_batch_processor(
    processor_type: str = "static",
    **kwargs
) -> BatchProcessor:
    """Factory function to create batch processor"""
    if processor_type == "dynamic":
        return DynamicBatchProcessor(**kwargs)
    else:
        return BatchProcessor(**kwargs)