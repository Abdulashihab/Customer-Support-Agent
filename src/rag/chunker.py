from pathlib import Path

# The docs folder is in the main project folder.
# This file is src/rag/chunker.py, so the project folder is 2 levels up.
DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


def split_document(text, source):
    """Cut one document into chunks: one chunk for each '## ' section."""
    title = source
    section = "Introduction"
    lines = []
    sections = []   # a list of (section name, lines of that section)

    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            sections.append((section, lines))
            section, lines = line[3:].strip(), []
        else:
            lines.append(line)
    sections.append((section, lines))

    chunks = []
    for name, body_lines in sections:
        body = "\n".join(body_lines).strip()
        if not body:
            continue   # skip empty sections
        chunks.append({
            "id": f"{source}::{len(chunks) + 1}",
            "source": source,
            "title": title,
            "section": name,
            "text": f"{title} - {name}\n{body}",
        })
    return chunks


def load_chunks(docs_dir=None):
    """Read every .md file in the docs folder and return all the chunks."""
    docs_dir = Path(docs_dir or DOCS_DIR)
    chunks = []
    for path in sorted(docs_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        chunks.extend(split_document(text, path.name))
    return chunks


if __name__ == "__main__":
    all_chunks = load_chunks()
    print(f"Documents folder: {DOCS_DIR}")
    print(f"Total chunks: {len(all_chunks)}\n")
    for chunk in all_chunks[:3]:
        print("-" * 50)
        print(chunk["id"])
        print(chunk["text"])