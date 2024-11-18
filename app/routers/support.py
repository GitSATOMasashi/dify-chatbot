from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database

router = APIRouter(
    prefix="/support",
    tags=["support"]
)

@router.get("/")
async def get_support():
    return {"message": "Support endpoint"} 