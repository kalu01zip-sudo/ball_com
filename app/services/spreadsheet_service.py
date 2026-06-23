import re
import csv
import httpx
from io import StringIO
from typing import List, Dict, Any

class SpreadsheetService:

    @staticmethod
    def _extract_doc_id(url: str) -> str | None:
        """Extracts the Google Sheet ID from a URL."""
        sheet_match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if sheet_match:
            return sheet_match.group(1)
        return None

    @classmethod
    async def fetch_public_csv(cls, url: str) -> str | None:
        """
        Downloads the public Google Sheet as CSV.
        """
        doc_id = cls._extract_doc_id(url)
        if not doc_id:
            raise ValueError("Invalid Google Sheets URL")
            
        export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv"

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(export_url)
            if response.status_code != 200:
                raise ValueError("Failed to fetch document. Is it public?")
            # Check if we got a login page instead of the actual document
            if "accounts.google.com/ServiceLogin" in response.url.path or "Sign in" in response.text[:200]:
                raise ValueError("Document is not public.")
            return response.text

    @classmethod
    async def fetch_oauth_csv(cls, url: str, access_token: str) -> str | None:
        """
        Downloads a private Google Sheet using an OAuth access token.
        """
        doc_id = cls._extract_doc_id(url)
        if not doc_id:
            raise ValueError("Invalid Google Sheets URL")
            
        # For Google Drive API v3, export to CSV
        export_url = f"https://www.googleapis.com/drive/v3/files/{doc_id}/export?mimeType=text/csv"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(export_url, headers=headers)
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch document via OAuth: {response.text}")
            return response.text

    @classmethod
    async def refresh_google_token(cls, refresh_token: str) -> str:
        """
        Uses the refresh_token to get a fresh access_token from Google.
        """
        from app.core.config import settings
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(token_url, data=data)
            if response.status_code != 200:
                raise ValueError(f"Failed to refresh Google token: {response.text}")
                
            return response.json().get("access_token")

    @classmethod
    async def watch_spreadsheet(cls, url: str, access_token: str, channel_id: str, webhook_url: str):
        """
        Registers a webhook to watch for changes on a Google Sheet.
        """
        doc_id = cls._extract_doc_id(url)
        if not doc_id:
            raise ValueError("Invalid Google Sheets URL")
            
        watch_url = f"https://www.googleapis.com/drive/v3/files/{doc_id}/watch"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "id": channel_id,
            "type": "web_hook",
            "address": webhook_url
        }
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(watch_url, headers=headers, json=payload)
            if response.status_code not in (200, 204):
                raise ValueError(f"Failed to setup watch: {response.text}")
            
            return response.json()

    @classmethod
    async def stop_watch(cls, access_token: str, channel_id: str, resource_id: str):
        """
        Stops an existing webhook watch channel on Google Drive.
        """
        stop_url = "https://www.googleapis.com/drive/v3/channels/stop"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "id": channel_id,
            "resourceId": resource_id
        }
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(stop_url, headers=headers, json=payload)
            if response.status_code not in (200, 204):
                raise ValueError(f"Failed to stop watch: {response.text}")
                
            return True

    @classmethod
    def parse_csv_reversed(cls, csv_text: str) -> List[Dict[str, Any]]:
        """
        Parses CSV text into a list of dictionaries, reversed (bottom to up),
        excluding rows where 'Supplier Link' is empty or missing.
        """
        f = StringIO(csv_text)
        reader = csv.DictReader(f)
        data = []
        for i, row in enumerate(reader):
            supplier_link = row.get("Supplier Link", "").strip()
            if supplier_link:
                row["row_index"] = i
                data.append(row)
        
        # Reverse the data
        data.reverse()
        return data

    @staticmethod
    def extract_asin_and_country(url: str):
        asin_match = re.search(r'/(?:dp|gp/product|exec/obidos/ASIN)/([A-Z0-9]{10})', url)
        domain_match = re.search(r'https?://(?:www\.)?amazon\.([a-z\.]+)/', url)
        
        asin = asin_match.group(1) if asin_match else None
        domain = domain_match.group(1) if domain_match else None
        
        tld_to_country = {
            "com": "US", "co.uk": "GB", "nl": "NL", "de": "DE", "fr": "FR",
            "it": "IT", "es": "ES", "ca": "CA", "co.jp": "JP", "in": "IN",
            "com.au": "AU", "com.br": "BR", "com.mx": "MX", "sg": "SG",
            "com.tr": "TR", "ae": "AE", "sa": "SA", "pl": "PL", "se": "SE",
            "com.be": "BE", "eg": "EG", "co.za": "ZA", "ie": "IE"
        }
        country_code = tld_to_country.get(domain) if domain else None
        
        return asin, country_code
