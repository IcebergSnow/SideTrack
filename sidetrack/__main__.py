import uvicorn

# Callback query strings contain authorization codes. Do not access-log them.
uvicorn.run("sidetrack.app:app", host="127.0.0.1", port=8000, access_log=False)
