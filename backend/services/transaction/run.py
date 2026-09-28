"""Run Transaction Service microservice."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "services.transaction.main:app",
        host="0.0.0.0",
        port=8102,
        reload=True,
    )
