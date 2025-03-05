from aiko2.storage import SimpleKnowledgeBase
import numpy as np

def main():
    kb = SimpleKnowledgeBase("test", dimension=368)

    N = 1000
    vectors = np.random.rand(N, 368)
    contents = [f"content_{i}" for i in range(N)]
    for content, vector in zip(contents, vectors):
        value = {"content": content}
        kb.insert(value, vector)

    query_vector = np.random.rand(368)
    result = kb.query(query_vector, top_k=10)
    print(result[0].value)

    kb.save()

    kb_2 = SimpleKnowledgeBase("test", dimension=368)
    kb_2.load()
    result_2 = kb_2.query(query_vector, top_k=10)

    all_equal = True
    for r1, r2 in zip(result, result_2):
        if r1.value["content"] != r2.value["content"]:
            all_equal = False
            break

    print(f"all_equal: {all_equal}")

if __name__ == "__main__":
    main()

    