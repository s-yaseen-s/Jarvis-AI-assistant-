"""Google Calendar tools for J.A.R.V.I.S.

Provides full Google Calendar integration for reading, creating, updating,
and deleting events. Requires OAuth2 credentials setup.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from fury import create_tool

CREDS_FILE = Path("credentials.json")
TOKEN_FILE  = Path("token.json")
SCOPES      = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    """Get or create authenticated Google Calendar service.
    
    Handles OAuth2 authentication and token refresh.
    Requires credentials.json in project root.
    
    Returns:
        Google Calendar API service object
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

    return build("calendar", "v3", credentials=creds)


def _fmt_event(e: dict) -> dict:
    """Format a raw Google Calendar event into readable format.
    
    Args:
        e: Raw event dict from Google Calendar API
        
    Returns:
        Formatted event dict with standard fields
    """
    start = e.get("start", {})
    end   = e.get("end", {})
    return {
        "id":          e.get("id", ""),
        "title":       e.get("summary", "(No title)"),
        "start":       start.get("dateTime", start.get("date", "")),
        "end":         end.get("dateTime", end.get("date", "")),
        "location":    e.get("location", ""),
        "description": e.get("description", ""),
        "link":        e.get("htmlLink", ""),
    }


# ── List upcoming events ─────────────────────────────────────────────────────

def list_events_tool():
    """Create a tool for listing upcoming Google Calendar events.
    
    Returns:
        Fury tool object for listing events
    """
    def list_events(days: int = 7, max_results: int = 20):
        """List upcoming Google Calendar events within a time range.
        
        Args:
            days: How many days ahead to look (default: 7)
            max_results: Maximum number of events to return (default: 20)
            
        Returns:
            Dict with events list, count, and range in days
        """
        try:
            svc  = _get_service()
            now  = datetime.now(timezone.utc)
            end  = now + timedelta(days=days)
            res  = svc.events().list(
                calendarId   = "primary",
                timeMin      = now.isoformat(),
                timeMax      = end.isoformat(),
                maxResults   = max_results,
                singleEvents = True,
                orderBy      = "startTime",
            ).execute()
            events = [_fmt_event(e) for e in res.get("items", [])]
            return {"events": events, "count": len(events), "range_days": days}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="list_calendar_events",
        description="List upcoming Google Calendar events. Default: next 7 days.",
        execute=list_events,
        input_schema={
            "type": "object",
            "properties": {
                "days":        {"type": "integer", "description": "How many days ahead to look (default 7)"},
                "max_results": {"type": "integer", "description": "Max events to return (default 20)"},
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "events": {"type": "array"},
                "count":  {"type": "integer"},
            },
            "required": [],
        },
    )


# ── Get today's events ───────────────────────────────────────────────────────

def today_events_tool():
    """Create a tool for getting today's Google Calendar events.
    
    Returns:
        Fury tool object for getting today's events
    """
    def get_today():
        """Get all Google Calendar events for today.
        
        Returns:
            Dict with events list, count, and date string
        """
        try:
            svc   = _get_service()
            now   = datetime.now(timezone.utc)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end   = start + timedelta(days=1)
            res   = svc.events().list(
                calendarId   = "primary",
                timeMin      = start.isoformat(),
                timeMax      = end.isoformat(),
                singleEvents = True,
                orderBy      = "startTime",
            ).execute()
            events = [_fmt_event(e) for e in res.get("items", [])]
            return {"events": events, "count": len(events), "date": start.strftime("%Y-%m-%d")}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="get_today_events",
        description="Get all Google Calendar events for today.",
        execute=get_today,
        input_schema={"type": "object", "properties": {}, "required": []},
        output_schema={
            "type": "object",
            "properties": {
                "events": {"type": "array"},
                "count":  {"type": "integer"},
                "date":   {"type": "string"},
            },
            "required": [],
        },
    )


# ── Create event ─────────────────────────────────────────────────────────────

def create_event_tool():
    """Create a tool for adding new Google Calendar events.
    
    Returns:
        Fury tool object for creating events
    """
    def create_event(title: str, start: str, end: str,
                     description: str = "", location: str = ""):
        """Create a new Google Calendar event.
        
        Args:
            title: Event title
            start: Start datetime in ISO 8601 format:
                   - Timed: "2025-06-20T14:00:00"
                   - All-day: "2025-06-20"
            end: End datetime in ISO 8601 format (same format as start)
            description: Optional event description
            location: Optional event location
            
        Returns:
            Dict with success status, event ID, title, and calendar link
        """
        try:
            svc = _get_service()
            # Detect all-day vs timed
            if "T" in start:
                start_obj = {"dateTime": start, "timeZone": "Africa/Cairo"}
                end_obj   = {"dateTime": end,   "timeZone": "Africa/Cairo"}
            else:
                start_obj = {"date": start}
                end_obj   = {"date": end}

            body = {"summary": title, "start": start_obj, "end": end_obj}
            if description: body["description"] = description
            if location:    body["location"]    = location

            event = svc.events().insert(calendarId="primary", body=body).execute()
            return {
                "success": True,
                "id":      event.get("id"),
                "title":   event.get("summary"),
                "link":    event.get("htmlLink"),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    return create_tool(
        id="create_calendar_event",
        description=(
            "Create a new Google Calendar event. "
            "Use ISO 8601 for start/end: '2025-06-20T14:00:00' (timed) or '2025-06-20' (all-day)."
        ),
        execute=create_event,
        input_schema={
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "Event title"},
                "start":       {"type": "string", "description": "Start datetime (ISO 8601)"},
                "end":         {"type": "string", "description": "End datetime (ISO 8601)"},
                "description": {"type": "string", "description": "Optional event description"},
                "location":    {"type": "string", "description": "Optional location"},
            },
            "required": ["title", "start", "end"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "id":      {"type": "string"},
                "title":   {"type": "string"},
                "link":    {"type": "string"},
            },
            "required": [],
        },
    )


# ── Delete event ─────────────────────────────────────────────────────────────

def delete_event_tool():
    """Create a tool for deleting Google Calendar events.
    
    Returns:
        Fury tool object for deleting events
    """
    def delete_event(event_id: str):
        """Delete a Google Calendar event by its ID.
        
        Args:
            event_id: The unique event ID to delete
            
        Returns:
            Dict with success status and deleted event ID
        """
        try:
            svc = _get_service()
            svc.events().delete(calendarId="primary", eventId=event_id).execute()
            return {"success": True, "deleted_id": event_id}
        except Exception as e:
            return {"error": str(e), "success": False}

    return create_tool(
        id="delete_calendar_event",
        description="Delete a Google Calendar event by its ID.",
        execute=delete_event,
        input_schema={
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The event ID to delete"},
            },
            "required": ["event_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success":    {"type": "boolean"},
                "deleted_id": {"type": "string"},
            },
            "required": [],
        },
    )


# ── Update event ─────────────────────────────────────────────────────────────

def update_event_tool():
    """Create a tool for updating Google Calendar events.
    
    Returns:
        Fury tool object for updating events
    """
    def update_event(event_id: str, title: str = "", start: str = "",
                     end: str = "", description: str = "", location: str = ""):
        """Update an existing Google Calendar event.
        
        Args:
            event_id: The unique event ID to update (required)
            title: New event title (optional)
            start: New start datetime in ISO 8601 format (optional)
            end: New end datetime in ISO 8601 format (optional)
            description: New event description (optional)
            location: New event location (optional)
            
        Returns:
            Dict with success status, updated event ID, and title
        """
        try:
            svc   = _get_service()
            event = svc.events().get(calendarId="primary", eventId=event_id).execute()
            if title:       event["summary"]     = title
            if description: event["description"] = description
            if location:    event["location"]    = location
            if start:
                if "T" in start:
                    event["start"] = {"dateTime": start, "timeZone": "Africa/Cairo"}
                else:
                    event["start"] = {"date": start}
            if end:
                if "T" in end:
                    event["end"] = {"dateTime": end, "timeZone": "Africa/Cairo"}
                else:
                    event["end"] = {"date": end}

            updated = svc.events().update(
                calendarId="primary", eventId=event_id, body=event).execute()
            return {"success": True, "id": updated["id"], "title": updated.get("summary")}
        except Exception as e:
            return {"error": str(e), "success": False}

    return create_tool(
        id="update_calendar_event",
        description="Update an existing Google Calendar event. Only provide fields you want to change.",
        execute=update_event,
        input_schema={
            "type": "object",
            "properties": {
                "event_id":    {"type": "string", "description": "Event ID to update"},
                "title":       {"type": "string", "description": "New title"},
                "start":       {"type": "string", "description": "New start datetime (ISO 8601)"},
                "end":         {"type": "string", "description": "New end datetime (ISO 8601)"},
                "description": {"type": "string", "description": "New description"},
                "location":    {"type": "string", "description": "New location"},
            },
            "required": ["event_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "id":      {"type": "string"},
                "title":   {"type": "string"},
            },
            "required": [],
        },
    )