"""Day 06 第一个实验：手工给定向量，只练习比较数字，不冒充模型输出。

运行：uv run python -m day06.vector_basics
"""

from math import sqrt


def normalize(vector: list[float]) -> list[float]:
    length = sqrt(sum(value * value for value in vector))
    if length == 0:
        raise ValueError("零向量没有方向，不能做这个余弦比较")
    return [value / length for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("两个向量的维度必须相同")
    left = normalize(left)
    right = normalize(right)
    return sum(a * b for a, b in zip(left, right))


def main() -> None:
    print("以下数字是人工设计的教学数据，没有调用 Embedding 模型。")
    query = [1.0, 0.0]
    examples = [
        ("网络资料", [0.8, 0.6]),
        ("关门资料", [0.0, 1.0]),
    ]
    print(f"假设问题的向量是 {query}")
    for label, vector in examples:
        print(f"{label} {vector} -> 余弦分数 {cosine(query, vector):.3f}")
    print("这只说明给定数字的方向关系，不能证明模型懂得网络或关门。")


if __name__ == "__main__":
    main()
