#!/usr/bin/env python3
"""
Test script for the refactored reranking service
"""
import asyncio
import time
import logging
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_provider_factory():
    """Test provider factory and sentence transformers provider"""
    from providers.provider_factory import ProviderFactory
    from config import RerankingProvider

    logger.info("Testing Provider Factory...")

    factory = ProviderFactory()

    # Get available providers
    providers = factory.get_available_providers()
    logger.info(f"Available providers: {providers['available']}")

    # Create sentence transformers provider
    try:
        provider = await factory.create_provider(
            provider_type=RerankingProvider.SENTENCE_TRANSFORMERS,
            model_name="cross-encoder/ms-marco-MiniLM-L-12-v2",
            device="cpu",
            cache_dir="./test_model_cache"
        )
        logger.info("✓ Provider created successfully")

        # Test reranking
        query = "What is artificial intelligence?"
        documents = [
            "Artificial intelligence (AI) is the simulation of human intelligence in machines.",
            "The weather today is sunny and warm.",
            "Machine learning is a subset of artificial intelligence.",
            "Pizza is a popular Italian dish."
        ]

        result = await provider.rerank(
            query=query,
            documents=documents,
            top_k=2,
            normalize_scores=True
        )

        logger.info(f"✓ Reranking successful:")
        logger.info(f"  Top documents: {result['documents'][:2]}")
        logger.info(f"  Scores: {result['scores'][:2]}")

        await provider.close()

    except Exception as e:
        logger.error(f"❌ Provider test failed: {e}")
        return False

    return True

async def test_cache_manager():
    """Test cache manager with LRU cache"""
    from cache.cache_manager import CacheManager

    logger.info("\nTesting Cache Manager...")

    # Create cache manager
    cache = CacheManager(
        cache_type="lru",
        cache_size=100,
        ttl=60
    )

    await cache.initialize()
    logger.info("✓ Cache initialized")

    # Test cache operations
    key = cache.generate_key("test query", ["doc1", "doc2"])

    # Test miss
    result = await cache.get(key)
    assert result is None, "Expected cache miss"
    logger.info("✓ Cache miss handled correctly")

    # Test set
    test_data = {"documents": ["doc1"], "scores": [0.9], "indices": [0]}
    await cache.set(key, test_data)
    logger.info("✓ Data cached")

    # Test hit
    result = await cache.get(key)
    assert result == test_data, "Cache data mismatch"
    logger.info("✓ Cache hit successful")

    # Get stats
    stats = await cache.get_stats()
    logger.info(f"✓ Cache stats: hits={stats['hits']}, misses={stats['misses']}")

    # Clear cache
    await cache.clear()
    logger.info("✓ Cache cleared")

    return True

async def test_request_models():
    """Test request and response models"""
    from models.requests import RerankRequest, BatchRerankRequest

    logger.info("\nTesting Request Models...")

    # Test single rerank request
    try:
        request = RerankRequest(
            query="test query",
            documents=["doc1", "doc2", "doc3"],
            top_k=2,
            normalize_scores=True
        )
        logger.info(f"✓ RerankRequest created: {request.query}")

        # Test batch request
        batch_request = BatchRerankRequest(
            queries=["query1", "query2"],
            documents_list=[["doc1", "doc2"], ["doc3", "doc4"]],
            top_k=1
        )
        logger.info(f"✓ BatchRerankRequest created: {len(batch_request.queries)} queries")

    except Exception as e:
        logger.error(f"❌ Request model test failed: {e}")
        return False

    return True

async def test_fallback_mechanism():
    """Test fallback mechanism with invalid model"""
    from providers.provider_factory import ProviderFactory
    from config import RerankingProvider

    logger.info("\nTesting Fallback Mechanism...")

    factory = ProviderFactory()

    try:
        # Try to create provider with non-existent model
        provider = await factory.create_provider(
            provider_type=RerankingProvider.SENTENCE_TRANSFORMERS,
            model_name="non-existent-model",
            device="cpu"
        )
        logger.error("❌ Should have failed with non-existent model")
        return False

    except RuntimeError as e:
        logger.info(f"✓ Correctly failed with non-existent model: {e}")

    return True

async def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Starting Reranking Service Tests")
    logger.info("=" * 60)

    tests = [
        ("Request Models", test_request_models),
        ("Cache Manager", test_cache_manager),
        ("Provider Factory", test_provider_factory),
        ("Fallback Mechanism", test_fallback_mechanism)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    total_passed = sum(1 for _, success in results if success)
    logger.info(f"\nTotal: {total_passed}/{len(results)} tests passed")

    return all(success for _, success in results)

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)