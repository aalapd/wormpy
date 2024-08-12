import PyPDF2
import io
import requests
import logging

def extract_text_from_pdf(file_path_or_url):
    """
    Extract text content from a PDF file.
    
    :param file_path_or_url: Local file path or URL of the PDF file
    :return: Extracted text content as a string
    """
    try:
        # Determine if the input is a URL or local file path
        if file_path_or_url.startswith(('http://', 'https://')):
            response = requests.get(file_path_or_url)
            response.raise_for_status()
            pdf_file = io.BytesIO(response.content)
        else:
            pdf_file = open(file_path_or_url, 'rb')

        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
        
        logging.info(f"Successfully extracted text from PDF: {file_path_or_url}")
        return text_content.strip()

    except Exception as e:
        logging.error(f"Error extracting text from PDF {file_path_or_url}: {str(e)}")
        return f"Error extracting text: {str(e)}"

    finally:
        if 'pdf_file' in locals() and not isinstance(pdf_file, io.BytesIO):
            pdf_file.close()

def is_pdf_url(url):
    """
    Check if the given URL points to a PDF file.
    
    :param url: URL to check
    :return: Boolean indicating if the URL is likely a PDF
    """
    return url.lower().endswith('.pdf') or 'application/pdf' in requests.head(url).headers.get('Content-Type', '')