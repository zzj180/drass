"""
Document processing task queue
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import httpx

from app.services.document_service import document_service
from app.services.vector_store import vector_store_service
from app.models.document import DocumentStatus, DocumentProcessingRequest

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Background document processing handler"""
    
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.workers = []
        self.num_workers = 3
        self.running = False
    
    async def start(self):
        """Start processing workers"""
        if self.running:
            return
        
        self.running = True
        
        # Start worker tasks
        for i in range(self.num_workers):
            worker = asyncio.create_task(self._process_worker(i))
            self.workers.append(worker)
        
        logger.info(f"Started {self.num_workers} document processing workers")
    
    async def stop(self):
        """Stop processing workers"""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to complete
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Stopped document processing workers")
    
    async def _process_worker(self, worker_id: int):
        """Worker task to process documents"""
        logger.info(f"Document processor worker {worker_id} started")
        
        while self.running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=1.0
                )
                
                await self._process_document_task(task, worker_id)
                
            except asyncio.TimeoutError:
                # No tasks available, continue
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
        
        logger.info(f"Document processor worker {worker_id} stopped")
    
    async def _process_document_task(self, task: Dict[str, Any], worker_id: int):
        """Process a single document task"""
        document_id = task.get('document_id')
        user_id = task.get('user_id')
        processing_request = task.get('processing_request')
        
        logger.info(f"Worker {worker_id} processing document {document_id}")
        
        try:
            # Process document
            result = await document_service.process_document(
                user_id=user_id,
                document_id=document_id,
                processing_request=processing_request
            )
            
            if result.status == DocumentStatus.COMPLETED:
                logger.info(f"Successfully processed document {document_id}")
                
                # Notify user if notification service is available
                try:
                    from app.services.notification_service import notification_service
                    await notification_service.send_notification(
                        user_id=user_id,
                        type="document_processed",
                        data={
                            "document_id": str(document_id),
                            "status": "completed",
                            "word_count": result.word_count,
                            "page_count": result.page_count
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to send notification: {e}")
            else:
                logger.warning(f"Document {document_id} processing failed: {result.error_message}")
                
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
    
    async def add_document_task(
        self,
        document_id: UUID,
        user_id: str,
        processing_request: Optional[DocumentProcessingRequest] = None
    ):
        """Add document to processing queue"""
        task = {
            'document_id': document_id,
            'user_id': user_id,
            'processing_request': processing_request,
            'created_at': datetime.utcnow()
        }
        
        await self.processing_queue.put(task)
        logger.debug(f"Added document {document_id} to processing queue")
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.processing_queue.qsize()
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status"""
        return {
            'running': self.running,
            'workers': len(self.workers),
            'queue_size': self.get_queue_size(),
            'active_workers': sum(1 for w in self.workers if not w.done())
        }


# Singleton instance
document_processor = DocumentProcessor()


async def process_document_batch(
    documents: list,
    user_id: str,
    processing_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process multiple documents in batch"""
    results = {
        'successful': [],
        'failed': [],
        'total': len(documents)
    }
    
    processing_request = None
    if processing_options:
        processing_request = DocumentProcessingRequest(**processing_options)
    
    # Add all documents to queue
    for doc_id in documents:
        try:
            await document_processor.add_document_task(
                document_id=doc_id,
                user_id=user_id,
                processing_request=processing_request
            )
            results['successful'].append(str(doc_id))
        except Exception as e:
            logger.error(f"Failed to queue document {doc_id}: {e}")
            results['failed'].append({
                'document_id': str(doc_id),
                'error': str(e)
            })
    
    return results


async def reprocess_failed_documents(user_id: str) -> Dict[str, Any]:
    """Reprocess all failed documents for a user"""
    from app.services.document_service import document_service
    
    # Get all failed documents
    failed_docs = []
    for doc in document_service.documents.values():
        if doc.user_id == user_id and doc.status == DocumentStatus.FAILED:
            failed_docs.append(doc.id)
    
    if not failed_docs:
        return {
            'message': 'No failed documents to reprocess',
            'count': 0
        }
    
    # Add to processing queue
    for doc_id in failed_docs:
        await document_processor.add_document_task(
            document_id=doc_id,
            user_id=user_id
        )
    
    return {
        'message': f'Queued {len(failed_docs)} documents for reprocessing',
        'count': len(failed_docs),
        'document_ids': [str(d) for d in failed_docs]
    }