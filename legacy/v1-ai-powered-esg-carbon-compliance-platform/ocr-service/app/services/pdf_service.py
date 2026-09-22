import fitz  # PyMuPDF
from pathlib import Path
import uuid

def convert_pdf_to_images(pdf_path: Path, output_dir: Path) -> list[Path]:
    """
    Converts a PDF file to a list of image files.
    Returns a list of Paths to the generated images.
    """
    image_paths = []
    
    # Open the PDF using PyMuPDF (no system dependencies required!)
    doc = fitz.open(pdf_path)
    
    for i in range(len(doc)):
        page = doc.load_page(i)
        # Render page to an image
        pix = page.get_pixmap()
        
        image_name = f"{uuid.uuid4()}_page_{i+1}.png"
        image_path = output_dir / image_name
        
        # Save the image
        pix.save(str(image_path))
        image_paths.append(image_path)
        
    return image_paths
