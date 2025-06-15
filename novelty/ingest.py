import os
import subprocess
import chromadb
from .novelty import _embed

CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma")
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection("papers")


def stream_pubmed(limit: int = 1_000_000, batch: int = 1000):
    query = "all[sb]"
    for start in range(0, limit, batch):
        cmd = (
            f"esearch -db pubmed -query '{query}' -retstart {start} -retmax {batch} "
            "| efetch -format abstract"
        )
        with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, text=True) as proc:
            abstract = []
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    if abstract:
                        yield " ".join(abstract)
                        abstract = []
                else:
                    abstract.append(line)
            if abstract:
                yield " ".join(abstract)
        if start + batch >= limit:
            break


def main():
    for idx, abstract in enumerate(stream_pubmed(), start=1):
        emb = _embed(abstract)
        collection.add(embeddings=[emb], ids=[f"pmid-{idx}"], documents=[abstract])
        if idx % 100 == 0:
            print(f"Ingested {idx}", flush=True)
        if idx >= 1_000_000:
            break


if __name__ == "__main__":
    main()
