import json
import os
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


load_dotenv()

app = FastAPI(title="Employee Assistant API")
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:8001", "http://127.0.0.1:8001"],
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"]
)


_repo_root = Path(__file__).resolve().parents[1]
_vector_dir = Path(__file__).resolve().parent / "vectorstore"
if not (_vector_dir / "embeddings.npy").exists():
	raise RuntimeError("Vector store is missing. Run build_vectorstore.py first.")

VS = load_vectorstore(_vector_dir)


def get_openai_client() -> OpenAI:
	api_key = os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise HTTPException(status_code=500, detail="OPENAI_KEY environment variable is not set")
	return OpenAI(api_key=api_key)


@app.get("/health")
def health() -> Dict[str, str]:
	return {"status": "ok"}


@app.get("/ask")
def ask(q: str, k: int = 5) -> JSONResponse:
	q = (q or "").strip()
	if not q:
		raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

	client = get_openai_client()
	model = VS["metadata"].get("model", "text-embedding-3-small")
	q_emb = client.embeddings.create(model=model, input=[q]).data[0].embedding
	q_emb_np = np.array(q_emb, dtype=np.float32)

	emb = VS["embeddings"]
	scores: List[float] = []
	for i in range(emb.shape[0]):
		scores.append(cosine_sim(q_emb_np, emb[i]))
	idxs = np.argsort(scores)[::-1][: max(1, min(k, len(scores)))]

	contexts: List[str] = []
	metas: List[Dict[str, Any]] = []
	for i in idxs:
		contexts.append(VS["texts"][int(i)])
		metas.append(VS["metadata"]["metadatas"][int(i)])

	prompt = (
		"You are a helpful assistant answering questions about employees. "
		"Use the provided context snippets. If the answer is not contained, say you don't know.\n\n"
		"Question: " + q + "\n\n" + "\n\n".join([f"Context {i+1}:\n" + c for i, c in enumerate(contexts)])
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

	return JSONResponse({
		"answer": answer,
		"contexts": contexts,
		"matches": metas
	})