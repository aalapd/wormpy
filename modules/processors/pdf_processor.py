import PyPDF2
import io
import requests
import logging
from urllib.parse import urlparse

def extract_text_from_pdf(file_path_or_url):
    """
    Extract text content from a PDF file.
    
    :param file_path_or_url: Local file path or URL of the PDF file
    :return: Extracted text content as a string
    """
    pdf_file = None
    try:
        # Determine if the input is a URL or local file path
        parsed = urlparse(file_path_or_url)
        if parsed.scheme in ('http', 'https'):
            response = requests.get(file_path_or_url)
            response.raise_for_status()
            pdf_file = io.BytesIO(response.content)
        else:
            pdf_file = open(file_path_or_url, 'rb')

        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text_content = "\n".join(page.extract_text() for page in pdf_reader.pages)
        
        logging.info(f"Successfully extracted text from PDF: {file_path_or_url}")
        return text_content.strip()

    except requests.RequestException as e:
        logging.error(f"Error fetching PDF from URL {file_path_or_url}: {str(e)}")
        return f"Error fetching PDF: {str(e)}"
    except PyPDF2.errors.PdfReadError as e:
        logging.error(f"Error reading PDF {file_path_or_url}: {str(e)}")
        return f"Error reading PDF: {str(e)}"
    except Exception as e:
        logging.error(f"Unexpected error processing PDF {file_path_or_url}: {str(e)}")
        return f"Unexpected error: {str(e)}"
    finally:
        if pdf_file and not isinstance(pdf_file, io.BytesIO):
            pdf_file.close()

def is_pdf_url(url):
    """
    Check if the given URL points to a PDF file.
    
    :param url: URL to check
    :return: Boolean indicating if the URL is likely a PDF
    """
    try:
        if url.lower().endswith('.pdf'):
            return True
        response = requests.head(url, allow_redirects=True)
        return 'application/pdf' in response.headers.get('Content-Type', '').lower()
    except requests.RequestException:
        logging.warning(f"Error checking content type for {url}")
        return False