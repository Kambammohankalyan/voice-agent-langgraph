import os
import time
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "voice-agent-memory"

# Initialize Pinecone & Embedder
if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)
else:
    pc = None
    print("⚠️ PINECONE_API_KEY missing. RAG will not work.")

print("⏳ Loading Embedding Model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def setup_index():
    """Creates Index if missing"""
    if not pc: return
    existing = [i.name for i in pc.list_indexes()]
    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME, 
            dimension=384, 
            metric="cosine", 
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        time.sleep(10) # Wait for AWS to provision

def ingest_file(filepath="data/knowledge_base.txt"):
    """Reads file and uploads to Pinecone (Batch Mode)"""
    if not pc: return
    setup_index()
    index = pc.Index(INDEX_NAME)
    
    with open(filepath, "r") as f:
        text = f.read()
    
    chunks = [c.strip() for c in text.split("\n") if c.strip()]
    vectors = []
    
    print(f"🚀 Ingesting {len(chunks)} facts...")
    for i, chunk in enumerate(chunks):
        vec = embedder.encode(chunk).tolist()
        # Use simple ID for initial batch
        vectors.append((str(i), vec, {"text": chunk}))
    
    index.upsert(vectors=vectors)
    print("✅ Memory Updated.")

def ingest_text(text):
    """
    NEW: Uploads a SINGLE fact immediately.
    Called by the 'save_user_info' tool in core.py.
    """
    if not pc: return
    setup_index()
    index = pc.Index(INDEX_NAME)
    
    print(f"💾 Real-time Ingestion: '{text}'")
    vec = embedder.encode(text).tolist()
    
    # Generate a unique ID based on time so we don't overwrite old facts
    unique_id = str(time.time())
    
    index.upsert(vectors=[(unique_id, vec, {"text": text})])
    print("✅ Fact Saved to Database.")

def retrieve(query):
    """Searches memory"""
    if not pc: return ""
    index = pc.Index(INDEX_NAME)
    vec = embedder.encode(query).tolist()
    
    results = index.query(vector=vec, top_k=3, include_metadata=True)
    return "\n".join([m['metadata']['text'] for m in results['matches']])

if __name__ == "__main__":
    # If run directly, it loads the file
    ingest_file()