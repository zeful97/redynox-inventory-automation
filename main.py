from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, database
from database import get_db

# Instruct SQLAlchemy to create the tables upon startup
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Redynox Zeful Inventory API", version="0.1.0")

# --- REST Endpoints ---

# 1. CREATE (POST)
@app.post("/items/", response_model=schemas.ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    # Business Logic: Check for duplicate serial numbers
    db_item = db.query(models.Item).filter(models.Item.serial_number == item.serial_number).first()
    if db_item:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Serial number already registered.")
    
    # Write to DB
    new_item = models.Item(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

# 2. READ ALL (GET)
@app.get("/items/", response_model=list[schemas.ItemResponse], status_code=status.HTTP_200_OK)
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Item).offset(skip).limit(limit).all()

# 3. READ SINGLE (GET)
@app.get("/items/{item_id}", response_model=schemas.ItemResponse, status_code=status.HTTP_200_OK)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested hardware asset not found.")
    return item

# 4. UPDATE (PUT)
@app.put("/items/{item_id}", response_model=schemas.ItemResponse, status_code=status.HTTP_200_OK)
def update_item(item_id: int, updated_item: schemas.ItemCreate, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested hardware asset not found.")
    
    for key, value in updated_item.model_dump().items():
        setattr(item, key, value)
        
    db.commit()
    db.refresh(item)
    return item

# 5. DELETE (DELETE)
@app.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested hardware asset not found.")
    
    db.delete(item)
    db.commit()
    return {"message": f"Asset {item_id} successfully deleted."}