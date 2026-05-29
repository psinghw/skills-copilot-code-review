"""Announcement endpoints for the High School Management System API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def _require_teacher(username: Optional[str]) -> Dict[str, Any]:
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def _normalize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": document["_id"],
        "title": document["title"],
        "message": document["message"],
        "start_date": document.get("start_date"),
        "end_date": document["end_date"],
        "created_by": document.get("created_by"),
    }


def _validate_dates(start_date: Optional[str], end_date: str) -> None:
    try:
        end_value = datetime.fromisoformat(end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Expiration date must be a valid ISO datetime") from exc

    if start_date:
        try:
            start_value = datetime.fromisoformat(start_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Start date must be a valid ISO datetime") from exc

        if start_value > end_value:
            raise HTTPException(status_code=400, detail="Start date must be before the expiration date")


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_announcements(include_all: bool = Query(False)) -> List[Dict[str, Any]]:
    """Get announcements, returning only currently active ones by default."""
    now = datetime.utcnow().isoformat()

    if include_all:
        query: Dict[str, Any] = {}
    else:
        query = {
            "end_date": {"$gte": now},
            "$or": [
                {"start_date": None},
                {"start_date": {"$exists": False}},
                {"start_date": {"$lte": now}},
            ],
        }

    announcements = [
        _normalize_announcement(document)
        for document in announcements_collection.find(query).sort("end_date", 1)
    ]
    return announcements


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    title: str,
    message: str,
    end_date: str,
    teacher_username: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create a new announcement. Requires a signed-in teacher."""
    teacher = _require_teacher(teacher_username)

    title = title.strip()
    message = message.strip()
    if not title or not message:
        raise HTTPException(status_code=400, detail="Title and message are required")

    _validate_dates(start_date, end_date)

    announcement = {
        "_id": str(uuid4()),
        "title": title,
        "message": message,
        "start_date": start_date,
        "end_date": end_date,
        "created_by": teacher["username"],
    }
    announcements_collection.insert_one(announcement)
    return _normalize_announcement(announcement)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    title: str,
    message: str,
    end_date: str,
    teacher_username: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Update an existing announcement. Requires a signed-in teacher."""
    _require_teacher(teacher_username)

    title = title.strip()
    message = message.strip()
    if not title or not message:
        raise HTTPException(status_code=400, detail="Title and message are required")

    _validate_dates(start_date, end_date)

    result = announcements_collection.update_one(
        {"_id": announcement_id},
        {
            "$set": {
                "title": title,
                "message": message,
                "start_date": start_date,
                "end_date": end_date,
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    document = announcements_collection.find_one({"_id": announcement_id})
    return _normalize_announcement(document)


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, str]:
    """Delete an announcement. Requires a signed-in teacher."""
    _require_teacher(teacher_username)

    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}