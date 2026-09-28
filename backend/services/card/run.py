"""Run Card Service microservice."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "services.card.main:app",
        host="0.0.0.0",
        port=8103,
        reload=True,
    )
