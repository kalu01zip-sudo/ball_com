import re
import httpx
from typing import List, Dict

class GoogleDocService:
    
    @staticmethod
    def _extract_doc_id(url: str) -> str | None:
        """Extracts the Google Doc or Google Sheet ID from a URL."""
        # Check for Google Docs
        doc_match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", url)
        if doc_match:
            return doc_match.group(1)
        
        # Check for Google Sheets
        sheet_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
        if sheet_match:
            return sheet_match.group(1)
            
        return None

    @staticmethod
    def _is_sheet(url: str) -> bool:
        return "/spreadsheets/d/" in url

    @classmethod
    async def extract_text_from_public_doc(cls, url: str) -> str | None:
        """
        Downloads the public Google Doc or Google Sheet as text/csv.
        Returns the text content or None if failed.
        """
        doc_id = cls._extract_doc_id(url)
        if not doc_id:
            return None
            
        if cls._is_sheet(url):
            export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv"
        else:
            export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            try:
                response = await client.get(export_url)
                response.raise_for_status()
                # Check if we got a login page instead of the actual document
                if "accounts.google.com/ServiceLogin" in response.url.path or "Sign in" in response.text[:200]:
                    raise Exception("Document is not public.")
                return response.text
            except Exception as e:
                print(f"Failed to fetch Google Doc: {e}")
                return None

    @classmethod
    def parse_identifiers(cls, text: str) -> List[Dict[str, str]]:
        """
        Parses Amazon ASINs and URLs from text line by line.
        Returns a list of dictionaries with type ('url' or 'asin') and value.
        """
        # Matches Amazon URLs including amzn.to shortlinks
        url_pattern = r"(https?://(?:www\.)?amazon\.[a-z\.]+/(?:[^/]+/)?(?:dp|gp/product|exec/obidos/ASIN)/[A-Z0-9]{10}[^\s]*|https?://amzn\.to/[a-zA-Z0-9]+)"
        
        # Matches 10-character alphanumeric starting with B0, or 10-digit ISBNs
        asin_pattern = r"\bB[\dA-Z]{9}\b|\b\d{9}(?:X|\d)\b"
        
        results = []
        seen = set()
        
        for line in text.splitlines():
            # First try to find ASINs in the line
            asins = re.findall(asin_pattern, line)
            if asins:
                for a in asins:
                    if a not in seen:
                        results.append({"type": "asin", "value": a})
                        seen.add(a)
                # If we found ASINs on this row, skip extracting URLs from the same row to prevent duplicates
                continue
                
            # If no ASIN was found, try extracting URLs
            urls = re.findall(url_pattern, line)
            if urls:
                for u in urls:
                    if u not in seen:
                        results.append({"type": "url", "value": u})
                        seen.add(u)
                        
        return results

