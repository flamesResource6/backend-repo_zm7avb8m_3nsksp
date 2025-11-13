from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from database import db, create_document, get_documents
from bson import ObjectId
import os

app = FastAPI(title="Ocean of Houses API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas
class Property(BaseModel):
    title: str
    price: float
    location: str
    bedrooms: int
    bathrooms: int
    area_sqft: int = Field(..., gt=0)
    image: Optional[str] = None
    description: Optional[str] = None
    featured: bool = False


@app.get("/")
def root():
    return {"message": "Ocean of Houses API running"}


@app.get("/test")
def test():
    try:
        ok = db is not None
        info = {
            "backend": "ok",
            "database": "connected" if ok else "unavailable",
            "database_url": bool(os.getenv("DATABASE_URL")),
            "database_name": os.getenv("DATABASE_NAME"),
            "connection_status": "ok" if ok else "no db",
            "collections": []
        }
        if ok:
            info["collections"] = db.list_collection_names()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/properties")
def create_property(prop: Property):
    try:
        _id = create_document("property", prop)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/properties")
def list_properties(featured: Optional[bool] = None, limit: Optional[int] = 50):
    try:
        query = {}
        if featured is not None:
            query["featured"] = featured
        docs = get_documents("property", query, limit)
        for d in docs:
            d["id"] = str(d.pop("_id"))
            if "created_at" in d:
                d["created_at"] = d["created_at"].isoformat()
            if "updated_at" in d:
                d["updated_at"] = d["updated_at"].isoformat()
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/properties/{prop_id}")
def get_property(prop_id: str):
    try:
        doc = db["property"].find_one({"_id": ObjectId(prop_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Not found")
        doc["id"] = str(doc.pop("_id"))
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].isoformat()
        if "updated_at" in doc:
            doc["updated_at"] = doc["updated_at"].isoformat()
        return doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
