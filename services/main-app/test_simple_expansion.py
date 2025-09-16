#!/usr/bin/env python3
"""
简单测试5000字扩展功能
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chains.compliance_rag_chain import ComplianceRAGChain

def test_word_count():
    """
    测试字数统计功能
    """
    print("测试字数统计功能")
    print("-" * 40)

    rag_chain = ComplianceRAGChain()

    test_texts = [
        "这是一个测试文本。",  # 9个字
        "GDPR是欧盟的数据保护法规。",  # 12个字
        "企业数据合规管理是一个复杂的过程，需要从多个维度进行考虑。"  # 27个字
    ]

    for text in test_texts:
        count = rag_chain._count_chinese_words(text)
        print(f"文本: {text}")
        print(f"字数: {count}\n")

def test_expansion_logic():
    """
    测试扩展逻辑（不依赖LLM）
    """
    print("\n测试扩展逻辑")
    print("-" * 40)

    rag_chain = ComplianceRAGChain()

    # 测试_is_compliance_mode
    print(f"合规模式已启用: {rag_chain._is_compliance_mode()}")

    # 测试_format_response的逻辑路径
    test_response = {
        "answer": "这是一个简短的测试回答。",
        "context": []
    }

    # 临时修改方法以避免LLM调用
    original_method = rag_chain._ensure_minimum_word_count_sync

    def mock_expansion(answer, sources, min_words=None):
        """模拟扩展方法"""
        if min_words is None:
            min_words = 5000
        current_count = rag_chain._count_chinese_words(answer)
        if current_count < min_words:
            expanded = answer + "\n\n" + "扩展内容" * 1000  # 添加大量文本
            expanded += f"\n\n---\n📊 **字数统计**: {rag_chain._count_chinese_words(expanded)}字 (满足{min_words}字要求)"
            return expanded
        return answer

    rag_chain._ensure_minimum_word_count_sync = mock_expansion

    # 测试格式化响应
    formatted = rag_chain._format_response(test_response)
    answer = formatted["answer"]

    print(f"原始字数: {rag_chain._count_chinese_words(test_response['answer'])}")
    print(f"扩展后字数: {rag_chain._count_chinese_words(answer)}")
    print(f"包含字数统计: {'是' if '字数统计' in answer else '否'}")

    # 恢复原方法
    rag_chain._ensure_minimum_word_count_sync = original_method

def test_config():
    """
    测试配置设置
    """
    print("\n测试配置设置")
    print("-" * 40)

    from app.core.config import settings

    print(f"COMPLIANCE_MODE_ENABLED: {settings.COMPLIANCE_MODE_ENABLED}")
    print(f"COMPLIANCE_MIN_WORD_COUNT: {settings.COMPLIANCE_MIN_WORD_COUNT}")
    print(f"COMPLIANCE_ENABLE_EMOJI: {settings.COMPLIANCE_ENABLE_EMOJI}")
    print(f"COMPLIANCE_ENABLE_MARKDOWN: {settings.COMPLIANCE_ENABLE_MARKDOWN}")
    print(f"COMPLIANCE_MAX_EXPANSION_ATTEMPTS: {settings.COMPLIANCE_MAX_EXPANSION_ATTEMPTS}")

def main():
    """
    主测试函数
    """
    print("=" * 80)
    print("简单测试5000字扩展功能（不依赖LLM）")
    print("=" * 80)
    print()

    try:
        # 测试1: 字数统计
        test_word_count()

        # 测试2: 扩展逻辑
        test_expansion_logic()

        # 测试3: 配置
        test_config()

        print("\n" + "=" * 80)
        print("✅ 所有测试完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()