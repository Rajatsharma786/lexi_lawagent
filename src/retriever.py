from __future__ import annotations

import os
from typing import List

import torch    # type: ignore
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma   # type: ignore
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainFilter
from langchain_community.cross_encoders import HuggingFaceCrossEncoder   # type: ignore
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.text_splitter import RecursiveCharacterTextSplitter

from sentence_transformers import SentenceTransformer  # type: ignore
import pdfplumber
from doctr.io import DocumentFile   # type: ignore  
from doctr.models import ocr_predictor      # type: ignore

from redis_caching import RedisCache
cache = RedisCache()

from dotenv import load_dotenv
load_dotenv()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
EMBED_MODEL = "nlpaueb/legal-bert-base-uncased"

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
sentence_model = SentenceTransformer(EMBED_MODEL, device=DEVICE)
embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL,model_kwargs={"device": "cpu"})

def build_final_retriever_from_chroma(persist_dir: str, collection: str) -> ContextualCompressionRetriever:
    """Load a Chroma store and wrap it with LLM filter + cross-encoder rerank, like your notebook."""
    
    db = Chroma(
        persist_directory=persist_dir,
        collection_name=collection,
        embedding_function=embeddings
    )

    # Base similarity retriever
    base = db.as_retriever(search_type="similarity", search_kwargs={"k": 7})

    # LLM filter (keeps only query-relevant docs)
    filter_llm = LLMChainFilter.from_llm(llm=llm)

    # Cross-encoder reranker
    reranker = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-large",model_kwargs={"device": "cpu"})
    rerank_compressor = CrossEncoderReranker(model=reranker, top_n=3)

    # Compose: base -> LLM filter -> rerank
    compressed = ContextualCompressionRetriever(
        base_compressor=filter_llm,
        base_retriever=base
    )
    final = ContextualCompressionRetriever(
        base_compressor=rerank_compressor,
        base_retriever=compressed
    )
    return final

#uploaded pdf chunks retriever
def chunk_document_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split document into smaller chunks with overlap."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return text_splitter.split_text(text)

def get_relevant_chunks(chunks: List[str], query: str, top_k: int = 3) -> str:
    """Get most relevant chunks using local embedding similarity."""
    # Initialize sentence transformer locally
    
    model = sentence_model
    
    # Get embeddings
    chunk_embeddings = model.encode(chunks)
    query_embedding = model.encode([query])
    
    # Calculate similarities
    similarities = torch.nn.functional.cosine_similarity(
        torch.tensor(query_embedding), 
        torch.tensor(chunk_embeddings)
    )
    
    # Get top k chunks
    top_indices = similarities.argsort(descending=True)[:top_k]
    return "\n\n".join([chunks[i] for i in top_indices])

#extracting text from pdf or image
def extract_text_from_image(image_path: str) -> str:
    model = ocr_predictor(pretrained=True)
    doc = DocumentFile.from_images(image_path)
    result = model(doc)
    return result.render()

def extract_text_from_pdf(path: str) -> str:
    text_pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            text_pages.append(t)
    combined = "\n".join(text_pages)
    if combined.strip():
        return combined

    # fallback to OCR for scanned PDFs
    model = ocr_predictor(pretrained=True)
    doc = DocumentFile.from_pdf(path)
    result = model(doc)
    return result.render()

def extract_text_auto(path: str) -> str:
    cached_text = cache.get_cached_extraction(path)
    if cached_text:
        print("Using cached extraction")
        return cached_text
    ext = os.path.splitext(path)[1].lower()
    if ext in [".png", ".jpg", ".jpeg"]:
        extracted_text = extract_text_from_image(path)
    elif ext == ".pdf":
        extracted_text =  extract_text_from_pdf(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    
    cache.cache_extraction(path, extracted_text)
    print("Cached new extraction")
    return extracted_text