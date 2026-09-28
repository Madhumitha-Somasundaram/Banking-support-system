"""Run Account Service microservice."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "services.account.main:app",
        host="0.0.0.0",
        port=8101,
        reload=True,
    )
