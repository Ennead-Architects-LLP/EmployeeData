import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
	an = a / (np.linalg.norm(a) + 1e-8)
	bn = b / (np.linalg.norm(b) + 1e-8)
	return float(np.dot(an, bn))


def load_vectorstore(vs_dir: Path) -> Dict[str, Any]:
	embeddings = np.load(vs_dir / "embeddings.npy")
	with (vs_dir / "metadata.json").open("r", encoding="utf-8") as f:
		metadata = json.load(f)
	with (vs_dir / "texts.json").open("r", encoding="utf-8") as f:
		texts: List[str] = json.load(f)
	return {"embeddings": embeddings, "metadata": metadata, "texts": texts}


def main() -> None:
	load_dotenv()
	parser = argparse.ArgumentParser(description="Answer a question using the employee vectorstore")
	parser.add_argument("--q", required=True, help="Question text")
	parser.add_argument("--k", type=int, default=5, help="Top-k contexts")
	args = parser.parse_args()

	api_key = os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise SystemExit("OPENAI_KEY environment variable is not set")
	client = OpenAI(api_key=api_key)

	vs_dir = Path(__file__).resolve().parent / "vectorstore"
	if not (vs_dir / "embeddings.npy").exists():
		raise SystemExit("Vector store missing. Build it first.")
	vs = load_vectorstore(vs_dir)

	model = vs["metadata"].get("model", "text-embedding-3-small")
	q_emb = client.embeddings.create(model=model, input=[args.q]).data[0].embedding
	q_emb_np = np.array(q_emb, dtype=np.float32)

	emb = vs["embeddings"]
	scores: List[float] = []
	for i in range(emb.shape[0]):
		scores.append(cosine_sim(q_emb_np, emb[i]))
	idxs = np.argsort(scores)[::-1][: max(1, min(args.k, len(scores)))]

	contexts: List[str] = []
	for i in idxs:
		contexts.append(vs["texts"][int(i)])

	prompt = (
		"You are a helpful assistant answering questions about employees. "
		"Use the provided context snippets. If the answer is not contained, say you don't know.\n\n"
		f"Question: {args.q}\n\n" + "\n\n".join([f"Context {i+1}:\n" + c for i, c in enumerate(contexts)])
	)
	chat = client.chat.completions.create(
		model="gpt-4o-mini",
		messages=[
			{"role": "system", "content": "You are concise."},
			{"role": "user", "content": prompt},
		],
		max_tokens=400
	)
	answer = chat.choices[0].message.content
	print(answer)


if __name__ == "__main__":
	main()
