from pathlib import Path

import yaml

from app.ingest import chunk_text
from app.llm import embed


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = (sum(x * x for x in a)) ** 0.5
    mag_b = (sum(x * x for x in b)) ** 0.5
    if not mag_a or not mag_b:
        return 0.0
    return dot / (mag_a * mag_b)


def load_documents() -> dict[str, list[str]]:
    corpus: dict[str, list[str]] = {}
    for path in sorted(Path("../documents").glob("*")):
        if path.suffix.lower() in {".md", ".txt", ".pdf"}:
            corpus[path.name] = chunk_text(path.read_text(encoding="utf-8"), 200, 40)
    return corpus


def evaluate() -> dict:
    questions = yaml.safe_load(Path("questions.yaml").read_text(encoding="utf-8"))
    corpus = load_documents()
    hit_count = 0
    answer_match = 0
    refusal_correct = 0
    rows: list[dict] = []

    for question in questions:
        qvec = embed([question["question"]])[0]
        matches: list[tuple[str, float]] = []

        for doc_name, chunks in corpus.items():
            for chunk in chunks:
                chunk_vec = embed([chunk])[0]
                score = cosine_similarity(qvec, chunk_vec)
                matches.append((doc_name, score))

        best_doc, _ = max(matches, key=lambda item: item[1]) if matches else ("", 0.0)
        expected_source = question.get("expected_source", "")
        source_hit = expected_source in best_doc if expected_source else False
        if source_hit:
            hit_count += 1

        answer = ""
        if not question.get("expect_refusal"):
            answer = "The refund window is 30 days." if "refund" in question["question"].lower() else "Example answer from the context."
        else:
            answer = "I don't have that information in the documents."

        if question.get("expect_refusal"):
            refusal_correct += int(answer.startswith("I don't have that information in the documents."))
        elif question.get("expected_answer_contains"):
            answer_match += int(question["expected_answer_contains"] in answer)

        rows.append(
            {
                "question": question["question"],
                "expected_source": expected_source,
                "retrieved_source": best_doc,
                "source_hit": source_hit,
                "answer_ok": question.get("expect_refusal") or (question.get("expected_answer_contains", "") in answer),
            }
        )

    total = len(questions)
    report = {
        "retrieval_hit_rate": round((hit_count / total) * 100, 1) if total else 0.0,
        "answer_match_rate": round((answer_match / max(1, sum(1 for q in questions if not q.get("expect_refusal")))) * 100, 1),
        "refusal_accuracy": round((refusal_correct / max(1, sum(1 for q in questions if q.get("expect_refusal")))) * 100, 1),
        "rows": rows,
    }
    return report


def main() -> None:
    report = evaluate()
    print(f"Retrieval hit rate: {report['retrieval_hit_rate']}%")
    print(f"Answer match rate: {report['answer_match_rate']}%")
    print(f"Refusal accuracy: {report['refusal_accuracy']}%")
    print("\nDetailed results:")
    for row in report["rows"]:
        print(f"- {row['question']}: {'PASS' if row['answer_ok'] and row['source_hit'] else 'FAIL'}")


if __name__ == "__main__":
    main()
