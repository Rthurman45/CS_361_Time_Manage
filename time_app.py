# Robert Thurman

from datetime import datetime, timedelta

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI(title="Tagalong")


app.mount("/design", StaticFiles(directory="design"), name="design")

templates = Jinja2Templates(directory="templates")


activities = []

joined_activities = []

current_user = "Guest"

# very simple in-memory account store: username -> password
# (IH#1 tagline + IH#2 privacy note live in templates/index.html near this form)
users = {}

preferences = {
    "text_size": "normal",
    "simple_view": False
}

CATEGORIES = ["Sports", "Food", "Games", "Other"]


# -----------------------------
# Helpers
# -----------------------------

def _filtered_activities(q: str, category: str):
    """IH#7 - two ways to find something: typed search OR category tabs."""
    results = activities
    if category and category != "ALL":
        results = [a for a in results if a["category"] == category]
    if q:
        q_lower = q.lower()
        results = [
            a for a in results
            if q_lower in a["name"].lower() or q_lower in a["description"].lower()
        ]
    return results


def _build_ics(activity: dict) -> str:
    try:
        start = datetime.strptime(f"{activity['date']} {activity['time']}", "%Y-%m-%d %H:%M")
    except ValueError:
        start = datetime.now()
    end = start + timedelta(hours=1)
    fmt = "%Y%m%dT%H%M%S"
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Tagalong//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:activity-{activity['id']}@tagalong\r\n"
        f"DTSTART:{start.strftime(fmt)}\r\n"
        f"DTEND:{end.strftime(fmt)}\r\n"
        f"SUMMARY:{activity['name']}\r\n"
        f"LOCATION:{activity['location']}\r\n"
        f"DESCRIPTION:{activity['description']}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


# -----------------------------
# Web App Home / Feed
# -----------------------------

@app.get("/app")
def home(request: Request):

    q = request.query_params.get("q", "")
    cat = request.query_params.get("cat", "ALL")
    err = request.query_params.get("err")
    joined_id = request.query_params.get("joined")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "activities": _filtered_activities(q, cat),
            "joined": joined_activities,
            "preferences": preferences,
            "current_user": current_user,
            "categories": CATEGORIES,
            "q": q,
            "cat": cat,
            "err": err,
            "missing_field": request.query_params.get("missing"),
            "joined_id": int(joined_id) if joined_id else None,
            "form_name": request.query_params.get("name", ""),
            "form_category": request.query_params.get("form_category", ""),
            "form_date": request.query_params.get("date", ""),
            "form_time": request.query_params.get("time", ""),
            "form_location": request.query_params.get("location", ""),
            "form_description": request.query_params.get("description", ""),
        }
    )


# -----------------------------
# Login
# -----------------------------

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    global current_user

    username = username.strip()

    # Reliability: never let a blank/garbage submission silently "succeed"
    if not username or not password:
        return RedirectResponse("/app?err=login_missing", status_code=303)

    if username in users:
        if users[username] != password:
            return RedirectResponse("/app?err=login_bad", status_code=303)
    else:
        # first time we see this username, register it
        users[username] = password

    current_user = username

    return RedirectResponse("/app", status_code=303)


# -----------------------------
# Create Activity
# -----------------------------

@app.post("/create")
def create_activity(
    name: str = Form(""),
    category: str = Form(""),
    date: str = Form(""),
    time: str = Form(""),
    location: str = Form(""),
    description: str = Form("")
):
    # IH#8 - tinker mindfully: every required field is checked server-side too,
    # not just the client-side `required` attribute, and the user gets their
    # entered values back instead of losing their work.
    missing = None
    if not name:
        missing = "name"
    elif not category:
        missing = "category"
    elif not date:
        missing = "date"
    elif not time:
        missing = "time"
    elif not location:
        missing = "location"

    if missing:
        return RedirectResponse(
            f"/app?err=post&missing={missing}&name={name}&form_category={category}"
            f"&date={date}&time={time}&location={location}&description={description}",
            status_code=303
        )

    activity = {
        "id": len(activities) + 1,
        "name": name,
        "category": category,
        "date": date,
        "time": time,
        "location": location,
        "description": description,
        "host": current_user,
        "important": False
    }

    activities.append(activity)

    return RedirectResponse("/app", status_code=303)


# -----------------------------
# Join Activity
# -----------------------------

@app.post("/join/{activity_id}")
def join(activity_id: int):

    for activity in activities:
        if activity["id"] == activity_id:
            if activity not in joined_activities:
                joined_activities.append(activity)

    return RedirectResponse(f"/app?joined={activity_id}", status_code=303)


# -----------------------------
# Leave Activity (also serves as "Undo" right after joining)
# -----------------------------

@app.post("/leave/{activity_id}")
def leave(activity_id: int):

    for activity in joined_activities:
        if activity["id"] == activity_id:
            joined_activities.remove(activity)
            break

    return RedirectResponse("/app", status_code=303)


# -----------------------------
# Calendar export (.ics) - Interoperability: standard iCalendar file
# that Google Calendar / Apple Calendar / Outlook can all import.
# -----------------------------

@app.get("/calendar/{activity_id}.ics")
def calendar_export(activity_id: int):

    for activity in joined_activities:
        if activity["id"] == activity_id:
            return Response(
                content=_build_ics(activity),
                media_type="text/calendar",
                headers={"Content-Disposition": f"attachment; filename=activity-{activity_id}.ics"}
            )

    return Response(content="Activity not found", status_code=404)


# -----------------------------
# Accessibility Settings
# -----------------------------

@app.post("/settings")
def settings(
    text_size: str = Form(...),
    simple_view: str = Form(None)
):

    preferences["text_size"] = text_size

    preferences["simple_view"] = simple_view == "on"

    return RedirectResponse("/app", status_code=303)


# -----------------------------
# API routes still available
# -----------------------------

@app.get("/feed")
def feed():

    return activities


@app.get("/joined")
def joined():

    return joined_activities


@app.get("/health")
def health():

    return {
        "status": "ok"
    }