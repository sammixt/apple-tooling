from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.stat import StatCreate, StatUpdate, Stat
from app.db.models import Stat as StatModel

router = APIRouter()

@router.post("/stats/", response_model=Stat)
def create_stat(stat: StatCreate, db: Session = Depends(get_db)):
    db_stat = StatModel(**stat.dict())
    db.add(db_stat)
    db.commit()
    db.refresh(db_stat)
    return db_stat

@router.get("/stats/{stat_id}", response_model=Stat)
def read_stat(stat_id: int, db: Session = Depends(get_db)):
    db_stat = db.query(StatModel).filter(StatModel.id == stat_id).first()
    if db_stat is None:
        raise HTTPException(status_code=404, detail="Stat not found")
    return db_stat

@router.put("/stats/{stat_id}", response_model=Stat)
def update_stat(stat_id: int, stat: StatUpdate, db: Session = Depends(get_db)):
    db_stat = db.query(StatModel).filter(StatModel.id == stat_id).first()
    if db_stat is None:
        raise HTTPException(status_code=404, detail="Stat not found")
    for key, value in stat.dict(exclude_unset=True).items():
        setattr(db_stat, key, value)
    db.commit()
    db.refresh(db_stat)
    return db_stat

@router.delete("/stats/{stat_id}", response_model=Stat)
def delete_stat(stat_id: int, db: Session = Depends(get_db)):
    db_stat = db.query(StatModel).filter(StatModel.id == stat_id).first()
    if db_stat is None:
        raise HTTPException(status_code=404, detail="Stat not found")
    db.delete(db_stat)
    db.commit()
    return db_stat
