def build_prompt(question: str, contexts: list[dict]) -> tuple[str, str]:
    if not contexts:
        return (
            "You are an internal documentation assistant. Answer the user's question using ONLY the context provided below. If the context does not contain the answer, reply exactly: \"I don't have that information in the documents.\"",
            question,
        )

    formatted_context = []
    for idx, context in enumerate(contexts, start=1):
        formatted_context.append(
            f"[{idx}] Source: {context['filename']} | Page: {context['page'] or 'N/A'}\n{context['snippet']}"
        )

    system = (
        "You are an internal documentation assistant. Answer the user's question using ONLY the context provided below. "
        "Every claim must be supported by the context. If the context does not contain the answer, reply exactly: \"I don't have that information in the documents.\" "
        "Do not use outside knowledge.\n\nContext:\n" + "\n---\n".join(formatted_context)
    )
    return system, question
