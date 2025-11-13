from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime
import uuid

app = FastAPI(title="CitizenConnect 2.0 API")

# CORS for development/preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Category = Literal[
    "Roads",
    "Water",
    "Electricity",
    "Health",
    "Education",
    "Sanitation",
    "Public Transport",
    "Waste Management",
    "Safety",
    "Others",
]

Priority = Literal["High", "Medium", "Low"]
Level = Literal["Local", "State", "Central"]
Status = Literal["Pending", "In Progress", "Resolved"]


class Location(BaseModel):
    lat: float
    lng: float


class ComplaintIn(BaseModel):
    user_id: str
    text: str
    voice_url: Optional[str] = None
    category: Category
    priority: Priority
    level: Level
    district: Optional[str] = None
    location: Optional[Location] = None
    assigned_to: Optional[str] = None


class Complaint(ComplaintIn):
    complaint_id: str
    status: Status = "Pending"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Demo in-memory store (replace with database in production)
DB: Dict[str, Complaint] = {}


@app.get("/")
def root():
    return {"message": "CitizenConnect 2.0 API running"}


@app.post("/complaints", response_model=Complaint)
def create_complaint(payload: ComplaintIn):
    cid = f"CC{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}"
    comp = Complaint(complaint_id=cid, **payload.model_dump())
    DB[cid] = comp
    return comp


@app.get("/complaints", response_model=List[Complaint])
def list_complaints(status: Optional[Status] = None):
    items = list(DB.values())
    if status:
        items = [c for c in items if c.status == status]
    # newest first
    items.sort(key=lambda x: x.timestamp, reverse=True)
    return items


class StatusUpdate(BaseModel):
    status: Status


@app.patch("/complaints/{complaint_id}", response_model=Complaint)
def update_status(complaint_id: str, payload: StatusUpdate):
    comp = DB.get(complaint_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    comp.status = payload.status
    DB[complaint_id] = comp
    return comp


@app.get("/stats")
def stats():
    total = len(DB)
    pending = len([c for c in DB.values() if c.status == "Pending"])
    in_progress = len([c for c in DB.values() if c.status == "In Progress"])
    resolved = len([c for c in DB.values() if c.status == "Resolved"])
    by_category: Dict[str, int] = {}
    for c in DB.values():
        by_category[c.category] = by_category.get(c.category, 0) + 1
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "by_category": by_category,
    }
