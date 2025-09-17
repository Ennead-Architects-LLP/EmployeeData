import json
import os
from pathlib import Path
from typing import List, Dict, Any, Union

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


def load_employees(employees_json_path: Path) -> List[Any]:
	with employees_json_path.open("r", encoding="utf-8") as f:
		data = json.load(f)
		# Accept either a list directly or an object containing a list
		if isinstance(data, dict):
			# Try common keys
			for key in ("employees", "data", "items", "people"):
				val = data.get(key)
				if isinstance(val, list):
					return val
			# Fallback to values list
			return list(data.values())
		elif isinstance(data, list):
			return data
		else:
			return []


def employee_to_text(employee: Union[Dict[str, Any], str]) -> str:
	if isinstance(employee, str):
		return employee.strip()
	if not isinstance(employee, dict):
		return ""

	parts: List[str] = []
	name = employee.get("name") or employee.get("full_name") or employee.get("Full Name")
	if name:
		parts.append(f"Name: {name}")
	title = employee.get("position") or employee.get("title")
	if title:
		parts.append(f"Title: {title}")
	phone = employee.get("phone") or employee.get("Phone")
	if phone:
		parts.append(f"Phone: {phone}")
	email = employee.get("email") or employee.get("Email")
	if email:
		parts.append(f"Email: {email}")
	projects = employee.get("projects") or employee.get("Projects")
	if isinstance(projects, list) and projects:
		parts.append("Projects: " + "; ".join([str(p) for p in projects]))
	bio = employee.get("bio") or employee.get("Bio")
	if bio:
		parts.append(f"Bio: {bio}")
	education = employee.get("education") or employee.get("Education")
	if isinstance(education, list) and education:
		parts.append("Education: " + "; ".join([str(e) for e in education]))
	licenses = employee.get("licenses") or employee.get("Licenses")
	if isinstance(licenses, list) and licenses:
		parts.append("Licenses: " + "; ".join([str(l) for l in licenses]))
	# Fallback: include everything stringifiable to improve recall
	if not parts:
		parts.append(" ".join([f"{k}: {v}" for k, v in employee.items() if isinstance(v, (str, int, float))]))
	return "\n".join([p for p in parts if p])


def ensure_dir(path: Path) -> None:
	path.mkdir(parents=True, exist_ok=True)


def main() -> None:
	load_dotenv()
	api_key = os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise RuntimeError("OPENAI_KEY environment variable is not set")

	client = OpenAI(api_key=api_key)

	repo_root = Path(__file__).resolve().parents[1]
	employees_json = repo_root / "docs" / "assets" / "employees.json"
	if not employees_json.exists():
		raise FileNotFoundError(f"employees.json not found at {employees_json}")

	vectorstore_dir = Path(__file__).resolve().parent / "vectorstore"
	ensure_dir(vectorstore_dir)

	employees = load_employees(employees_json)
	texts: List[str] = []
	metas: List[Dict[str, Any]] = []
	for idx, emp in enumerate(employees):
		text = employee_to_text(emp)
		if not text or not text.strip():
			continue
		texts.append(text)
		name = None
		email = None
		if isinstance(emp, dict):
			name = emp.get("name") or emp.get("full_name") or emp.get("Full Name")
			email = emp.get("email") or emp.get("Email")
		metas.append({
			"index": idx,
			"name": name,
			"email": email,
		})

	if not texts:
		raise RuntimeError("No valid employee entries found to embed")

	model = "text-embedding-3-small"

	embeddings: List[List[float]] = []
	batch_size = 64
	for start in range(0, len(texts), batch_size):
		batch = texts[start:start + batch_size]
		resp = client.embeddings.create(model=model, input=batch)
		for item in resp.data:
			embeddings.append(item.embedding)

	emb_array = np.array(embeddings, dtype=np.float32)
	np.save(vectorstore_dir / "embeddings.npy", emb_array)
	with (vectorstore_dir / "metadata.json").open("w", encoding="utf-8") as f:
		json.dump({"metadatas": metas, "model": model}, f, ensure_ascii=False)
	with (vectorstore_dir / "texts.json").open("w", encoding="utf-8") as f:
		json.dump(texts, f, ensure_ascii=False)

	print(f"Built vector store with {len(texts)} entries at {vectorstore_dir}")


if __name__ == "__main__":
	main()
