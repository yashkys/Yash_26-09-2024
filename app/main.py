from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Annotated
from . import models
from .database import engine, SessionLocal
from sqlalchemy.orm import Session
from .report_servcie import trigger_report_creation, get_report_info
from .log import errorLog

app = FastAPI()
models.Base.metadata.create_all(bind = engine)


def get_db() :
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        errorLog(f"Error connecting databse: {e}")
    # finally:
    #     db.close()


db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/", status_code=status.HTTP_200_OK)
async def initApp():
    return {"message": "Store Management"}


@app.post("/trigger_report/", status_code=status.HTTP_200_OK)
async def trigger_report():
    report_id = trigger_report_creation()
    return {"report_id": report_id}

@app.get("/report/{report_id}", status_code=status.HTTP_200_OK)
async def get_report(report_id, db: db_dependency):
    info = get_report_info(report_id)
    # db_user = models.User(**user.dict())
    # db.add(db_user)
    # db.commit()
    return  info