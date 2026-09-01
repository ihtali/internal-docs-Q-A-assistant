from app.retrieve import _vector_literal, score_similarity


def test_score_similarity_returns_between_zero_and_one():
    score = score_similarity(0.9, 0.1)
    assert 0.0 <= score <= 1.0


def test_vector_literal_converts_python_list_to_pgvector_string():
    vector_text = _vector_literal([0.1, 0.2, 0.3])
    assert vector_text == "[0.1,0.2,0.3]"
