"""Gmail tools for J.A.R.V.I.S.

Provides full Gmail integration for listing, reading, searching, and sending emails.
Uses Gmail API with OAuth2 authentication.
"""

import base64
import re
from pathlib import Path
from email.mime.text import MIMEText
from fury import create_tool

CREDS_FILE = Path("credentials.json")
TOKEN_FILE  = Path("gmail_token.json")
SCOPES      = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


def _get_service():
    """Get or create authenticated Gmail API service.
    
    Handles OAuth2 authentication and token refresh.
    Requires credentials.json in project root.
    
    Returns:
        Google Gmail API service object
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _decode_body(payload: dict) -> str:
    """Extract plain-text body from a message payload.
    
    Recursively searches through MIME parts to find text content.
    Converts HTML to plain text by stripping tags.
    
    Args:
        payload: Message payload dict from Gmail API
        
    Returns:
        Plain text email body
    """
    def _decode(data: str) -> str:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    mime = payload.get("mimeType", "")
    body = payload.get("body", {})

    if mime == "text/plain" and body.get("data"):
        return _decode(body["data"])

    if mime == "text/html" and body.get("data"):
        html = _decode(body["data"])
        # Strip HTML tags for plain text
        return re.sub(r'<[^>]+>', ' ', html).strip()

    for part in payload.get("parts", []):
        result = _decode_body(part)
        if result:
            return result

    return ""


def _header(headers: list, name: str) -> str:
    """Extract a specific header value from message headers.
    
    Case-insensitive header name matching.
    
    Args:
        headers: List of header dicts from Gmail API
        name: Header name to find (e.g., 'From', 'Subject')
        
    Returns:
        Header value, or empty string if not found
    """
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _fmt_message(msg: dict, full: bool = False) -> dict:
    """Format a Gmail message for output.
    
    Extracts and organizes key email fields into a readable dict.
    
    Args:
        msg: Raw message dict from Gmail API
        full: If True, include full email body; else include only snippet
        
    Returns:
        Formatted message dict with id, from, to, subject, date, body/snippet
    """
    headers = msg.get("payload", {}).get("headers", [])
    result  = {
        "id":      msg["id"],
        "from":    _header(headers, "From"),
        "to":      _header(headers, "To"),
        "subject": _header(headers, "Subject"),
        "date":    _header(headers, "Date"),
        "snippet": msg.get("snippet", ""),
    }
    if full:
        result["body"] = _decode_body(msg.get("payload", {}))
    return result


# ── List recent emails ──────────────────────────────────────────────────────

def list_emails_tool():
    """Create a tool for listing recent emails from Gmail.
    
    Returns:
        Fury tool object for listing emails
    """
    def list_emails(count: int = 5, label: str = "INBOX"):
        """List the most recent emails from Gmail inbox or label.
        
        Args:
            count: Number of emails to retrieve (default: 5)
            label: Gmail label/folder to search (default: INBOX)
            
        Returns:
            Dict with emails list and count
        """
        try:
            svc  = _get_service()
            res  = svc.users().messages().list(
                userId="me", maxResults=count, labelIds=[label]).execute()
            ids  = [m["id"] for m in res.get("messages", [])]
            msgs = []
            for mid in ids:
                m = svc.users().messages().get(
                    userId="me", id=mid, format="metadata",
                    metadataHeaders=["From", "To", "Subject", "Date"]).execute()
                msgs.append(_fmt_message(m))
            return {"emails": msgs, "count": len(msgs)}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="list_emails",
        description="List the most recent emails from Gmail inbox.",
        execute=list_emails,
        input_schema={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of emails to retrieve (default 5)"},
                "label": {"type": "string",  "description": "Gmail label/folder (default INBOX)"},
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "emails": {"type": "array"},
                "count":  {"type": "integer"},
            },
            "required": [],
        },
    )


# ── Read full email ─────────────────────────────────────────────────────────

def read_email_tool():
    """Create a tool for reading the full body of an email.
    
    Returns:
        Fury tool object for reading emails
    """
    def read_email(email_id: str):
        """Read the full body of a specific email by its ID.
        
        Args:
            email_id: The Gmail message ID to retrieve
            
        Returns:
            Dict with id, from, to, subject, date, and full body text
        """
        try:
            svc = _get_service()
            msg = svc.users().messages().get(
                userId="me", id=email_id, format="full").execute()
            return _fmt_message(msg, full=True)
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="read_email",
        description="Read the full body of a specific email by its ID.",
        execute=read_email,
        input_schema={
            "type": "object",
            "properties": {
                "email_id": {"type": "string", "description": "The Gmail message ID"},
            },
            "required": ["email_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "id":      {"type": "string"},
                "from":    {"type": "string"},
                "subject": {"type": "string"},
                "body":    {"type": "string"},
            },
            "required": [],
        },
    )


# ── Search emails ───────────────────────────────────────────────────────────

def search_emails_tool():
    """Create a tool for searching Gmail using Gmail search syntax.
    
    Returns:
        Fury tool object for searching emails
    """
    def search_emails(query: str, count: int = 10):
        """Search Gmail using Gmail search syntax.
        
        Args:
            query: Gmail search query (e.g., 'from:boss', 'subject:invoice', 'is:unread')
            count: Maximum number of results to return (default: 10)
            
        Returns:
            Dict with matching emails list, count, and search query
        """
        try:
            svc = _get_service()
            res = svc.users().messages().list(
                userId="me", q=query, maxResults=count).execute()
            ids  = [m["id"] for m in res.get("messages", [])]
            msgs = []
            for mid in ids:
                m = svc.users().messages().get(
                    userId="me", id=mid, format="metadata",
                    metadataHeaders=["From", "To", "Subject", "Date"]).execute()
                msgs.append(_fmt_message(m))
            return {"emails": msgs, "count": len(msgs), "query": query}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="search_emails",
        description=(
            "Search Gmail using Gmail search syntax. "
            "Examples: 'from:boss@company.com', 'subject:invoice', 'is:unread', 'after:2024/01/01'."
        ),
        execute=search_emails,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query"},
                "count": {"type": "integer", "description": "Max results (default 10)"},
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "emails": {"type": "array"},
                "count":  {"type": "integer"},
            },
            "required": [],
        },
    )


# ── Send email ──────────────────────────────────────────────────────────────

def send_email_tool():
    """Create a tool for sending emails via Gmail.
    
    Returns:
        Fury tool object for sending emails
    """
    def send_email(to: str, subject: str, body: str):
        """Send an email via Gmail.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            body: Email body text (plain text)
            
        Returns:
            Dict with success status, sent message ID, recipient, and subject
        """
        try:
            svc  = _get_service()
            msg  = MIMEText(body)
            msg["to"]      = to
            msg["subject"] = subject
            raw  = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            sent = svc.users().messages().send(
                userId="me", body={"raw": raw}).execute()
            return {"success": True, "id": sent.get("id"), "to": to, "subject": subject}
        except Exception as e:
            return {"error": str(e), "success": False}

    return create_tool(
        id="send_email",
        description="Send an email via Gmail.",
        execute=send_email,
        input_schema={
            "type": "object",
            "properties": {
                "to":      {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body":    {"type": "string", "description": "Email body (plain text)"},
            },
            "required": ["to", "subject", "body"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "id":      {"type": "string"},
            },
            "required": [],
        },
    )