#Robert Thurman

"""
starting skeleton.
Fill in routes below as features are built.
"""
from fastapi import FastAPI
 
app = FastAPI(title="tagalong")
 
# TODO: signup / login
# TODO: post activity
# TODO: feed
# TODO: join / leave activity
 
 
@app.get("/health")
def health():
    return {"status": "ok"}
 
