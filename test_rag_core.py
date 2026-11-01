# test_rag_core.py
"""RAG 核心函数的单元测试。

跑法：python -m pytest test_rag_core.py -v
"""
import pytest
from rag_core import split_by_paragraph, cosine, rank_by_vectors


# ===== 切片 =====

def test_split_basic():
    """按空行切段，多余空行不产生空块。"""
    text = "第一段\n\n第二段\n\n\n第三段"
    assert split_by_paragraph(text) == ["第一段", "第二段", "第三段"]


def test_split_keeps_heading_with_content():
    """关键用例：标题必须和它的内容留在同一块。

    这是踩过的坑 —— 按固定字数硬切会把标题和金额劈到两个块里，
    导致含答案的那块字面命中为 0。
    """
    text = (
        "## 三、住宿费标准\n一线城市每晚不超过 600 元。\n\n"
        "## 四、餐饮补贴\n每天补贴 120 元。"
    )
    chunks = split_by_paragraph(text)

    assert "住宿费标准" in chunks[0]
    assert "600" in chunks[0], "标题和金额被拆开了"
    assert "餐饮补贴" in chunks[1]


# ===== 相似度 =====

def test_cosine_identical():
    """完全相同的向量，相似度为 1。"""
    assert cosine([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_cosine_opposite():
    """方向相反的向量，相似度为 -1。"""
    assert cosine([1, 0], [-1, 0]) == pytest.approx(-1.0)


def test_cosine_perpendicular():
    """垂直的两个向量，相似度为 0。"""
    assert cosine([1, 0], [0, 1]) == pytest.approx(0.0)


def test_cosine_zero_vector():
    """零向量没有方向，相似度应为 0，而不是让程序崩溃。"""
    assert cosine([0, 0], [1, 2]) == 0.0


# ===== 排序 =====

def test_rank_orders_by_score():
    """最相似的排第一，最不相似的排最后。"""
    qv = [1, 0]
    chunks = ["远", "近", "中"]
    vecs = [[0, 1], [1, 0.1], [1, 1]]

    result = rank_by_vectors(qv, chunks, vecs, top_k=3)

    assert result[0][1] == "近"
    assert result[-1][1] == "远"


def test_rank_respects_top_k():
    """top_k 限制返回条数。"""
    qv = [1, 0]
    chunks = ["a", "b", "c"]
    vecs = [[1, 0], [0.9, 0.1], [0, 1]]

    assert len(rank_by_vectors(qv, chunks, vecs, top_k=2)) == 2
