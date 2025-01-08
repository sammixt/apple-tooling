from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.file_content import FileContentCreate, FileContentUpdate, FileContent
from app.db.models import FileContent as FileContentModel

router = APIRouter()

@router.post("/file_contents/", response_model=FileContent)
def create_file_content(file_content: FileContentCreate, db: Session = Depends(get_db)):
    db_file_content = FileContentModel(**file_content.dict())
    db.add(db_file_content)
    db.commit()
    db.refresh(db_file_content)
    return db_file_content

@router.get("/file_contents/{file_content_id}", response_model=FileContent)
def read_file_content(file_content_id: int, db: Session = Depends(get_db)):
    db_file_content = db.query(FileContentModel).filter(FileContentModel.id == file_content_id).first()
    if db_file_content is None:
        raise HTTPException(status_code=404, detail="FileContent not found")
    return db_file_content

@router.put("/file_contents/{file_content_id}", response_model=FileContent)
def update_file_content(file_content_id: int, file_content: FileContentUpdate, db: Session = Depends(get_db)):
    db_file_content = db.query(FileContentModel).filter(FileContentModel.id == file_content_id).first()
    if db_file_content is None:
        raise HTTPException(status_code=404, detail="FileContent not found")
    for key, value in file_content.dict(exclude_unset=True).items():
        setattr(db_file_content, key, value)
    db.commit()
    db.refresh(db_file_content)
    return db_file_content

@router.delete("/file_contents/{file_content_id}", response_model=FileContent)
def delete_file_content(file_content_id: int, db: Session = Depends(get_db)):
    db_file_content = db.query(FileContentModel).filter(FileContentModel.id == file_content_id).first()
    if db_file_content is None:
        raise HTTPException(status_code=404, detail="FileContent not found")
    db.delete(db_file_content)
    db.commit()
    return db_file_content
