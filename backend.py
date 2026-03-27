from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import init_db, get_db, User, Event, EventParticipant

app = FastAPI()
init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_user_by_tg_id(db: Session, tg_id: int) -> Optional[User]:
    return db.query(User).filter(User.tg_id == tg_id).first()


@app.get("/schedule", response_class=HTMLResponse)
def schedule(request: Request, tg_id: int, db: Session = Depends(get_db)):
    user = get_user_by_tg_id(db, tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    events = db.query(Event).order_by(Event.datetime.asc()).all()

    participants_map = {}
    for ev in events:
        parts = (
            db.query(EventParticipant)
            .filter(EventParticipant.event_id == ev.id)
            .all()
        )
        participants_map[ev.id] = parts

    return templates.TemplateResponse(
        "schedule.html",
        {
            "request": request,
            "user": user,
            "events": events,
            "participants_map": participants_map,
        },
    )


@app.post("/events/create")
def create_event(
    tg_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    date: str = Form(...),   # YYYY-MM-DD
    time: str = Form(...),   # HH:MM
    db: Session = Depends(get_db),
):
    user = get_user_by_tg_id(db, tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    dt = datetime.fromisoformat(f"{date}T{time}")
    event = Event(
        owner_id=user.id,
        title=title,
        description=description,
        datetime=dt,
    )
    db.add(event)
    db.commit()

    return RedirectResponse(
        url=f"/schedule?tg_id={tg_id}", status_code=303
    )


@app.post("/events/{event_id}/join")
def join_event(
    event_id: int,
    tg_id: int = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user_by_tg_id(db, tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    participant = (
        db.query(EventParticipant)
        .filter(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user.id,
        )
        .first()
    )

    if not participant:
        participant = EventParticipant(
            event_id=event_id, user_id=user.id, status="going"
        )
        db.add(participant)
    else:
        participant.status = "going"

    db.commit()
    return RedirectResponse(
        url=f"/schedule?tg_id={tg_id}", status_code=303
    )


@app.post("/events/{event_id}/leave")
def leave_event(
    event_id: int,
    tg_id: int = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user_by_tg_id(db, tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    participant = (
        db.query(EventParticipant)
        .filter(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user.id,
        )
        .first()
    )

    if participant:
        db.delete(participant)
        db.commit()

    return RedirectResponse(
        url=f"/schedule?tg_id={tg_id}", status_code=303
    )