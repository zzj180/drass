#!/usr/bin/env python3
"""
测试5000字强制展开功能
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chains.compliance_rag_chain import ComplianceRAGChain
from app.core.config import settings

async def test_word_count_expansion():
    """
    测试字数扩展功能
    """
    print("=" * 80)
    print("测试5000字强制展开功能")
    print("=" * 80)

    # 初始化RAG链
    rag_chain = ComplianceRAGChain()

    # 测试短回答的扩展
    test_questions = [
        "什么是GDPR？",
        "企业如何进行数据合规管理？",
        "请详细说明数据安全的最佳实践"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n测试 {i}: {question}")
        print("-" * 40)

        try:
            # 调用RAG链
            result = await rag_chain.ainvoke({"query": question})

            answer = result.get("answer", "")

            # 统计字数
            word_count = rag_chain._count_chinese_words(answer)

            print(f"回答字数: {word_count}")
            print(f"满足5000字要求: {'✅ 是' if word_count >= 5000 else '❌ 否'}")

            # 显示部分回答内容
            preview_length = 500
            if len(answer) > preview_length:
                print(f"\n回答预览（前{preview_length}字）:")
                print(answer[:preview_length] + "...")
            else:
                print(f"\n完整回答:")
                print(answer)

            # 检查是否包含字数统计
            if "字数统计" in answer:
                print("\n✅ 包含字数统计信息")
            else:
                print("\n❌ 未包含字数统计信息")

        except Exception as e:
            print(f"❌ 测试失败: {e}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

async def test_direct_expansion():
    """
    直接测试扩展方法
    """
    print("\n" + "=" * 80)
    print("直接测试扩展方法")
    print("=" * 80)

    rag_chain = ComplianceRAGChain()

    # 测试短文本
    short_answer = """
    GDPR（General Data Protection Regulation，通用数据保护条例）是欧盟制定的一项重要的数据保护法规。
    它于2018年5月25日正式生效，旨在保护欧盟公民的个人数据和隐私权。
    GDPR对全球范围内处理欧盟居民个人数据的企业都有约束力。
    """

    print(f"原始文本字数: {rag_chain._count_chinese_words(short_answer)}")

    # 测试扩展
    expanded = await rag_chain._ensure_minimum_word_count(
        short_answer,
        [],
        min_words=5000
    )

    expanded_count = rag_chain._count_chinese_words(expanded)
    print(f"扩展后字数: {expanded_count}")
    print(f"满足要求: {'✅' if expanded_count >= 5000 else '❌'}")

    # 保存扩展结果
    output_file = "/tmp/expanded_answer.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(expanded)
    print(f"\n扩展结果已保存到: {output_file}")

async def test_config_override():
    """
    测试配置覆盖
    """
    print("\n" + "=" * 80)
    print("测试配置覆盖")
    print("=" * 80)

    # 临时修改配置
    original_value = settings.COMPLIANCE_MODE_ENABLED

    # 测试关闭合规模式
    settings.COMPLIANCE_MODE_ENABLED = False
    rag_chain = ComplianceRAGChain()

    result = await rag_chain.ainvoke({"query": "什么是API？"})
    answer = result.get("answer", "")
    word_count = rag_chain._count_chinese_words(answer)

    print(f"合规模式关闭时字数: {word_count}")
    print(f"是否扩展: {'是' if word_count >= 5000 else '否'}")

    # 恢复配置
    settings.COMPLIANCE_MODE_ENABLED = original_value

    # 测试开启合规模式
    settings.COMPLIANCE_MODE_ENABLED = True
    rag_chain2 = ComplianceRAGChain()

    result2 = await rag_chain2.ainvoke({"query": "什么是API？"})
    answer2 = result2.get("answer", "")
    word_count2 = rag_chain2._count_chinese_words(answer2)

    print(f"合规模式开启时字数: {word_count2}")
    print(f"是否扩展: {'是' if word_count2 >= 5000 else '否'}")

async def main():
    """
    主测试函数
    """
    try:
        # 测试1: 基本功能测试
        await test_word_count_expansion()

        # 测试2: 直接测试扩展方法
        await test_direct_expansion()

        # 测试3: 配置覆盖测试
        await test_config_override()

    except KeyboardInterrupt:
        print("\n\n测试被中断")
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())