#!/usr/bin/env python3
import os

import uvicorn

if __name__ == "__main__":
    # Host stays localhost: some browser features (e.g. desktop notifications)
    # require a secure context, which Chrome grants to localhost but not 0.0.0.0.
    # PORT defaults to 8000 for local dev; Conductor passes $CONDUCTOR_PORT so
    # multiple workspaces can run concurrently.
    uvicorn.run(
        "backend.main:app",
        host="localhost",
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
    )
