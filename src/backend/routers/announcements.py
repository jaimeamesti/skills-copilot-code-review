"""
Endpoints for announcement management in the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def is_announcement_active(announcement: Dict[str, Any]) -> bool:
    """Check if an announcement is currently active based on start and expiration dates"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if announcement has not expired
    if announcement.get("expiration_date") and announcement["expiration_date"] < today:
        return False
    
    # Check if announcement has started (if start_date is set)
    if announcement.get("start_date") and announcement["start_date"] > today:
        return False
    
    return True


@router.get("", response_model=List[Dict[str, Any]])
def get_announcements():
    """Get all active announcements (public endpoint, no auth required)"""
    announcements = []
    for announcement in announcements_collection.find():
        if is_announcement_active(announcement):
            # Convert ObjectId to string for JSON serialization
            announcement["_id"] = str(announcement["_id"])
            announcements.append(announcement)
    
    return announcements


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(username: Optional[str] = Query(None)):
    """Get all announcements (admin/signed-in users only) - includes expired/inactive ones"""
    # Check authentication
    if not username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action"
        )
    
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials"
        )
    
    announcements = []
    for announcement in announcements_collection.find():
        # Convert ObjectId to string for JSON serialization
        announcement["_id"] = str(announcement["_id"])
        announcements.append(announcement)
    
    return announcements


@router.post("/manage", response_model=Dict[str, Any])
def create_announcement(
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None,
    username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Create a new announcement (signed-in users only)"""
    # Check authentication
    if not username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action"
        )
    
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials"
        )
    
    # Validate dates
    try:
        exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid expiration date format. Use YYYY-MM-DD"
        )
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            if start > exp_date:
                raise HTTPException(
                    status_code=400, detail="Start date cannot be after expiration date"
                )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid start date format. Use YYYY-MM-DD"
            )
    
    # Create announcement
    announcement = {
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "created_by": username
    }
    
    result = announcements_collection.insert_one(announcement)
    
    if not result.inserted_id:
        raise HTTPException(
            status_code=500, detail="Failed to create announcement"
        )
    
    announcement["_id"] = str(result.inserted_id)
    return announcement


@router.put("/manage/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None,
    username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement (signed-in users only)"""
    # Check authentication
    if not username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action"
        )
    
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials"
        )
    
    # Validate dates
    try:
        exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid expiration date format. Use YYYY-MM-DD"
        )
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            if start > exp_date:
                raise HTTPException(
                    status_code=400, detail="Start date cannot be after expiration date"
                )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid start date format. Use YYYY-MM-DD"
            )
    
    # Convert string ID to ObjectId
    try:
        obj_id = ObjectId(announcement_id)
    except:
        raise HTTPException(
            status_code=400, detail="Invalid announcement ID"
        )
    
    # Update announcement
    update_data = {
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_by": username
    }
    
    result = announcements_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=404, detail="Announcement not found"
        )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=500, detail="Failed to update announcement"
        )
    
    # Fetch the updated announcement
    updated = announcements_collection.find_one({"_id": obj_id})
    updated["_id"] = str(updated["_id"])
    return updated


@router.delete("/manage/{announcement_id}", response_model=Dict[str, Any])
def delete_announcement(
    announcement_id: str,
    username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Delete an announcement (signed-in users only)"""
    # Check authentication
    if not username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action"
        )
    
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials"
        )
    
    # Convert string ID to ObjectId
    try:
        obj_id = ObjectId(announcement_id)
    except:
        raise HTTPException(
            status_code=400, detail="Invalid announcement ID"
        )
    
    result = announcements_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404, detail="Announcement not found"
        )
    
    return {"message": "Announcement deleted successfully", "deleted_count": result.deleted_count}
