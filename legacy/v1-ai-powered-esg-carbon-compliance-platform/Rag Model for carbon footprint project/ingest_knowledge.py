import os
import uuid
import re
from typing import List, Dict, Any
from pathlib import Path
import pandas as pd
from pypdf import PdfReader
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Qdrant Credentials
QDRANT_URL = "https://ad266743-7867-4a2b-9a80-9ae7d5e914a2.us-east-1-1.aws.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6NjY4ZGUzMmYtN2NlOC00Njg5LTkzOTItZmU4YzkyYTUzYTczIn0.S3MMzTZBL_oR3mZO5HWnPcz13sowlAZ-yd0Vx-YpHK8"

COLLECTION_NAME = "ghg_compliance_matrix"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIMENSION = 384
DATA_DIR = "Carbon Emissions"
BATCH_SIZE = 100

def get_metadata_from_filename(filename: str) -> Dict[str, str]:
    """Infer metadata such as topic, document_type, and version_year from filename."""
    lower_filename = filename.lower()
    
    # Document Type
    if filename.endswith(('.xlsx', '.xls')):
        document_type = 'Calculation Tool'
    elif 'guidance' in lower_filename:
        document_type = 'GHG Guidance'
    elif 'standard' in lower_filename:
        document_type = 'GHG Protocol Standard'
    else:
        document_type = 'ESG Document'
        
    # Topic
    if 'scope 2' in lower_filename:
        topic = 'Scope 2'
    elif 'scope3' in lower_filename or 'scope 3' in lower_filename:
        topic = 'Scope 3'
    elif 'uncertainty' in lower_filename:
        topic = 'Uncertainty'
    elif 'chp' in lower_filename:
        topic = 'CHP'
    elif 'global-warming-potential' in lower_filename:
        topic = 'GWP Values'
    elif 'hfc' in lower_filename or 'pfc' in lower_filename or 'cfc' in lower_filename:
        topic = 'Refrigerants'
    elif 'transport' in lower_filename:
        topic = 'Transport'
    elif 'stationary' in lower_filename:
        topic = 'Stationary Combustion'
    elif 'emission_factors' in lower_filename:
        topic = 'Emission Factors'
    else:
        topic = 'General GHG Protocol'
        
    # Version/Year extraction heuristically
    year_match = re.search(r'(19|20)\d{2}', filename)
    version_year = year_match.group(0) if year_match else 'Latest'
    
    return {
        "document_type": document_type,
        "topic": topic,
        "version_year": version_year
    }

def process_pdf(filepath: Path) -> List[Dict[str, Any]]:
    """Parse PDF file page by page to respect structural boundaries."""
    chunks = []
    metadata = get_metadata_from_filename(filepath.name)
    try:
        reader = PdfReader(str(filepath))
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                # Avoid splitting randomly; keep the whole page as a context chunk
                chunks.append({
                    "text": text.strip(),
                    "source_file": filepath.name,
                    "section": f"Page {page_num + 1}",
                    **metadata
                })
    except Exception as e:
        print(f"Error reading PDF {filepath.name}: {e}")
    return chunks

def process_excel(filepath: Path) -> List[Dict[str, Any]]:
    """Parse Excel files by flattening rows and grouping them into 10-row segments."""
    chunks = []
    metadata = get_metadata_from_filename(filepath.name)
    try:
        xls = pd.ExcelFile(str(filepath))
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            # Drop completely empty rows
            df.dropna(how='all', inplace=True)
            # Convert all to string to prevent float64 invalid value '' assignment
            df = df.astype(str)
            df = df.replace({'nan': '', 'None': ''})
            
            headers = [str(col) for col in df.columns]
            current_segment = []
            
            for index, row in df.iterrows():
                row_str = f"[Row {index}] " + ", ".join(
                    [f"{header}: {row[header]}" for header in headers if str(row[header]).strip()]
                )
                current_segment.append(row_str)
                
                # Group every 10 rows
                if len(current_segment) == 10:
                    chunks.append({
                        "text": "\n".join(current_segment),
                        "source_file": filepath.name,
                        "section": f"Sheet: {sheet_name}",
                        **metadata
                    })
                    current_segment = []
                    
            # Add remaining rows in the last segment
            if current_segment:
                chunks.append({
                    "text": "\n".join(current_segment),
                    "source_file": filepath.name,
                    "section": f"Sheet: {sheet_name}",
                    **metadata
                })
    except Exception as e:
        print(f"Error reading Excel {filepath.name}: {e}")
    return chunks

def get_all_chunks(directory: str) -> List[Dict[str, Any]]:
    """Iterate through the specified directory and parse files."""
    all_chunks = []
    path = Path(directory)
    if not path.exists():
        print(f"Directory {directory} not found. Please run this script in the correct root.")
        return []

    for file_path in path.rglob("*"):
        if file_path.suffix.lower() == '.pdf':
            print(f"Processing PDF: {file_path.name}")
            all_chunks.extend(process_pdf(file_path))
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            print(f"Processing Excel: {file_path.name}")
            all_chunks.extend(process_excel(file_path))
    return all_chunks

def setup_qdrant_and_upload(chunks: List[Dict[str, Any]]):
    """Embed chunks using FastEmbed and upload them to Qdrant Cloud."""
    if not chunks:
        print("No chunks to upload.")
        return
        
    print("Initializing Qdrant Client...")
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )
    
    # Recreate collection
    print(f"Recreating collection '{COLLECTION_NAME}'...")
    try:
        client.delete_collection(collection_name=COLLECTION_NAME)
    except Exception:
        pass
        
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=VECTOR_DIMENSION, 
            distance=models.Distance.COSINE
        )
    )

    print("Initializing FastEmbed Local Model...")
    embedding_model = TextEmbedding(EMBEDDING_MODEL_NAME)
    
    texts = [chunk["text"] for chunk in chunks]
    
    # Create generators for the batches
    for i in range(0, len(texts), BATCH_SIZE):
        batch_chunks = chunks[i:i + BATCH_SIZE]
        batch_texts = texts[i:i + BATCH_SIZE]
        
        print(f"Embedding and uploading batch {i // BATCH_SIZE + 1}...")
        
        # FastEmbed yields generator of np arrays.
        embeddings = list(embedding_model.embed(batch_texts))
        
        points = []
        for j, emb in enumerate(embeddings):
            chunk = batch_chunks[j]
            payload = {
                "source_file": chunk["source_file"],
                "document_type": chunk["document_type"],
                "section": chunk["section"],
                "topic": chunk["topic"],
                "version_year": chunk["version_year"],
                "text": chunk["text"]
            }
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=emb.tolist(),
                    payload=payload
                )
            )
            
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
    print("Ingestion completed successfully!")

if __name__ == "__main__":
    current_dir = Path(__file__).parent
    data_dir_path = current_dir / DATA_DIR
    chunks = get_all_chunks(str(data_dir_path))
    print(f"Total chunks extracted: {len(chunks)}")
    setup_qdrant_and_upload(chunks)
