import uvicorn

uvicorn.run("sidetrack.app:app", host="127.0.0.1", port=8000, access_log=False)
