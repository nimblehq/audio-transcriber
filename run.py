#!/usr/bin/env python3
import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="localhost", port=8000, reload=True)
