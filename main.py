from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from database import engine, Base, get_db
from cache import redis_client
import models
import schemas
import string
import random

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "URL Shortener API is running"}

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))

@app.post("/shorten", response_model=schemas.LinkResponse)
def shorten_url(link: schemas.LinkCreate, db: Session = Depends(get_db)):
    short_code = generate_short_code()

    db_link = models.Link(short_code=short_code, long_url=link.long_url)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    return db_link

@app.get("/links/{short_code}/stats")
def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    db_link = db.query(models.Link).filter(models.Link.short_code == short_code).first()

    if not db_link:
        raise HTTPException(status_code=404, detail="Short URL not found")

    total_clicks = db.query(models.Click).filter(models.Click.link_id == db_link.id).count()

    clicks_by_day = (
        db.query(
            sql_func.date(models.Click.timestamp).label("day"),
            sql_func.count(models.Click.id).label("count")
        )
        .filter(models.Click.link_id == db_link.id)
        .group_by(sql_func.date(models.Click.timestamp))
        .order_by(sql_func.date(models.Click.timestamp))
        .all()
    )

    return {
        "short_code": db_link.short_code,
        "long_url": db_link.long_url,
        "total_clicks": total_clicks,
        "clicks_by_day": [{"day": str(row.day), "count": row.count} for row in clicks_by_day]
    }

@app.get("/{short_code}")
def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    cached_url = redis_client.get(short_code)

    if cached_url:    
        print(f"CACHE HIT for {short_code}")
        long_url = cached_url
    else:
        print(f"CACHE MISS for {short_code} — querying DB")
        db_link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
        if not db_link:
            raise HTTPException(status_code=404, detail="Short URL not found")
        long_url = db_link.long_url
        redis_client.setex(short_code, 3600, long_url)

    link_row = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    click = models.Click(
        link_id=link_row.id,
        referrer=request.headers.get("referer")
    )
    db.add(click)
    db.commit()

    return RedirectResponse(url=long_url)
    