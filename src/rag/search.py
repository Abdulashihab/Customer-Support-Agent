from src.rag.ingest import get_collection


def search(question, n_results=3):
    """Find the cards that are closest in meaning to the question."""
    collection = get_collection()
    result = collection.query(query_texts=[question], n_results=n_results)

    cards = []
    for i in range(len(result["ids"][0])):
        cards.append({
            "id": result["ids"][0][i],
            "text": result["documents"][0][i],
            "source": result["metadatas"][0][i]["source"],
            "section": result["metadatas"][0][i]["section"],
            "distance": result["distances"][0][i],
        })
    return cards


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "my TV shows nothing"
    for card in search(question):
        print("-" * 50)
        print(f"{card['source']} / {card['section']}  (distance {card['distance']:.2f})")
        print(card["text"])