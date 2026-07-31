# Robert Thurman

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI(title="Tagalong")


app.mount("/design", StaticFiles(directory="design"), name="design")

templates = Jinja2Templates(directory="templates")


activities = []

joined_activities = []

current_user = "Guest"

preferences = {
    "text_size": "normal",
    "simple_view": False
}


# -----------------------------
# Web App Home
# -----------------------------

@app.get("/app")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "activities": activities,
            "joined": joined_activities,
            "preferences": preferences,
            "current_user": current_user
        }
    )

# -----------------------------
# Login
# -----------------------------

@app.post("/login")
def login(username: str = Form(...)):
    global current_user

    current_user = username
    
    return RedirectResponse(
        "/app",
        status_code=303
    )


# -----------------------------
# Create Activity
# -----------------------------

@app.post("/create")
def create_activity(
    name: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    location: str = Form(...),
    description: str = Form(...)
):

    if location == "": 
        return {
            "error": "Location required"
        }


    activity = {

        "id": len(activities) + 1,

        "name": name,

        "date": date,

        "time": time,

        "location": location,

        "description": description,

        "important": False

    }


    activities.append(activity)


    return RedirectResponse(
        "/app",
        status_code=303
    )



# -----------------------------
# Join Activity
# -----------------------------

@app.post("/join/{activity_id}")
def join(activity_id:int):

    for activity in activities:

        if activity["id"] == activity_id:

            if activity not in joined_activities:

                joined_activities.append(activity)


    return RedirectResponse(
        "/app",
        status_code=303
    )



# -----------------------------
# Leave Activity
# -----------------------------

@app.post("/leave/{activity_id}")
def leave(activity_id:int):

    for activity in joined_activities:

        if activity["id"] == activity_id:

            joined_activities.remove(activity)


    return RedirectResponse(
        "/app",
        status_code=303
    )



# -----------------------------
# Accessibility Settings
# -----------------------------

@app.post("/settings")
def settings(
    text_size:str = Form(...),
    simple_view:str = Form(None)
):

    preferences["text_size"] = text_size

    preferences["simple_view"] = simple_view == "on"


    return RedirectResponse(
        "/app",
        status_code=303
    )



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
        "status":"ok"
    }