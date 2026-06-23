from pydantic import BaseModel, Field

class ImportPublicLinkRequest(BaseModel):
    spreadsheet_url: str = Field(..., description="The public Google Spreadsheet URL")

class ImportOAuthRequest(BaseModel):
    spreadsheet_url: str = Field(..., description="The Google Spreadsheet URL")
    access_token: str = Field(..., description="Google OAuth access token for fetching private sheets")
    refresh_token: str = Field(None, description="Google OAuth refresh token for offline fetching")

class SetupWatchRequest(BaseModel):
    spreadsheet_url: str = Field(..., description="The Google Spreadsheet URL to watch")
    access_token: str = Field(..., description="Google OAuth access token for setting up the watch")
    refresh_token: str = Field(..., description="Google OAuth refresh token for offline fetching")

class StopWatchRequest(BaseModel):
    spreadsheet_url: str = Field(..., description="The Google Spreadsheet URL to stop watching")
    access_token: str = Field(..., description="Google OAuth access token to authorize the stop request")
