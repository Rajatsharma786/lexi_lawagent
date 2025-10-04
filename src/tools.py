from __future__ import annotations

import json
import os
from io import BytesIO
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.tools import tool
from langgraph.types import interrupt
from reportlab.lib.pagesizes import letter #type: ignore
from reportlab.pdfgen import canvas #type: ignore

from retriever import build_final_retriever_from_chroma
from redis_caching import RedisCache
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent


LAWS_DB_DIR = str(PROJECT_ROOT / "laws_db_chroma")
PROC_DB_DIR = str(PROJECT_ROOT / "procedures_db_chroma")
LAWS_COLL = "laws_db"
PROC_DB_DIR = "procedures_db_chroma"
PROC_COLL = "procedures_db"

# Build retrievers once
laws_retriever = build_final_retriever_from_chroma(LAWS_DB_DIR, LAWS_COLL)
procedures_retriever = build_final_retriever_from_chroma(PROC_DB_DIR, PROC_COLL)

cache = RedisCache()
redis_client = cache.redis_client

@tool("laws_db_lookup", return_direct=False)
def laws_db_lookup(query: str) -> List[Dict[str, Any]]:
    """Search Acts, regulations, and statutory instruments (Victoria). Returns a list of {meta, text}."""
    try:
        query_hash = cache.get_query_hash(query)
        cache_key = f"laws_query:{query_hash}"

        cached_result = redis_client.get(cache_key)
        if cached_result:
            print("Using cached law query result")
            try:
                print("exiting")
                return json.loads(cached_result)
            except json.JSONDecodeError:
                redis_client.delete(cache_key)
                
        print("Cache miss - retrieving from laws database")
        docs: List[Document] = laws_retriever.invoke(query)
        result = [{"metadata": d.metadata, "text": d.page_content} for d in docs]

        # Cache management
        if cache.check_memory_usage() > 25:
            cache.clear_old_cache()

        # Cache the new result with explicit expiration
        print("caching new result")
        redis_client.setex(
            cache_key,
            int(os.environ["REDIS_EXPIRATION"]),
            json.dumps(result)
        )
        return result
        
    except Exception as e:
        print(f"Error in laws_db_lookup: {str(e)}")
        docs = laws_retriever.invoke(query)
        return [{"metadata": d.metadata, "text": d.page_content} for d in docs]


@tool("procedures_db_lookup", return_direct=False)
def procedures_db_lookup(query: str) -> List[Dict[str, Any]]:
    """Search procedural forms and court application documents. Returns a list of {meta, text}."""
    try:
        docs: List[Document] = procedures_retriever.get_relevant_documents(query)
        result = [{"metadata": d.metadata, "text": d.page_content} for d in docs]
        return result
    except Exception as e:
        raise

@tool
def generate_court_form(
    title: str,
    subtitle: str = "Supreme Court of Victoria",
    fields: List[str] = None,
    instructions: str = ""
) -> str:
    """Generate a fillable PDF court form based on form type and required fields.
    
    Args:
        title: Form title (required)
        subtitle: Form subtitle (default: "Supreme Court of Victoria")
        fields: List of required fields for the form
        instructions: Any special instructions for completing the form
    """
    if fields is None:
        fields = [
            "Case Number",
            "Applicant's Name",
            "Respondent's Name",
            "Court Case Number",
            "Date of Filing",
            "Details of Opposition",
            "Grounds for Opposition",
            "Supporting Documents",
            "Contact Information"
        ]
    
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Add form fields
        c.setFont("Helvetica", 12)
        y = 750  # Starting y position
        
        # Add form title
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "SUPREME COURT OF VICTORIA")
        c.drawString(50, y-20, title)
        c.drawString(50, y-40, subtitle)
        
        # Add dynamic fields
        y = y - 80
        field_count = 0
        for field in fields:
            field_count += 1
            if y < 100:  # Start new page if needed
                c.showPage()
                y = 750
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, f"{field}:")
            c.setFont("Helvetica", 12)
            c.drawString(50, y-15, "_" * 70)
            y -= 40
            
        # Add instructions if provided
        if instructions:
            if y < 150:
                c.showPage()
                y = 750
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(50, y-20, "Instructions:")
            y -= 35
            for line in instructions.split("\n"):
                c.drawString(50, y, line)
                y -= 15
                
        c.save()
        
        # Save to file
        pdf_data = buffer.getvalue()
        filename = f"{title.lower().replace(' ', '_')}.pdf"
        with open(filename, "wb") as f:
            f.write(pdf_data)

        return f"✓ Form successfully generated and saved as: {filename}"
        
    except Exception as e:
        return f"✗ Error generating form: {str(e)}"