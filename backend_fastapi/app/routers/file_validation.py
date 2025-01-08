from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.file_validation import FileValidationCreate, FileValidationUpdate, FileValidation
from app.db.models import FileValidation as FileValidationModel

router = APIRouter()

@router.post("/file_validations/", response_model=FileValidation)
def create_file_validation(file_validation: FileValidationCreate, db: Session = Depends(get_db)):
    db_file_validation = FileValidationModel(**file_validation.dict())
    db.add(db_file_validation)
    db.commit()
    db.refresh(db_file_validation)
    return db_file_validation

@router.get("/file_validations/{file_validation_id}", response_model=FileValidation)
def read_file_validation(file_validation_id: int, db: Session = Depends(get_db)):
    db_file_validation = db.query(FileValidationModel).filter(FileValidationModel.id == file_validation_id).first()
    if db_file_validation is None:
        raise HTTPException(status_code=404, detail="FileValidation not found")
    return db_file_validation

@router.put("/file_validations/{file_validation_id}", response_model=FileValidation)
def update_file_validation(file_validation_id: int, file_validation: FileValidationUpdate, db: Session = Depends(get_db)):
    db_file_validation = db.query(FileValidationModel).filter(FileValidationModel.id == file_validation_id).first()
    if db_file_validation is None:
        raise HTTPException(status_code=404, detail="FileValidation not found")
    for key, value in file_validation.dict(exclude_unset=True).items():
        setattr(db_file_validation, key, value)
    db.commit()
    db.refresh(db_file_validation)
    return db_file_validation

@router.delete("/file_validations/{file_validation_id}", response_model=FileValidation)
def delete_file_validation(file_validation_id: int, db: Session = Depends(get_db)):
    db_file_validation = db.query(FileValidationModel).filter(FileValidationModel.id == file_validation_id).first()
    if db_file_validation is None:
        raise HTTPException(status_code=404, detail="FileValidation not found")
    db.delete(db_file_validation)
    db.commit()
    return db_file_validation
