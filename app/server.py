import os

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langchain_core.runnables import RunnableLambda
from langserve import add_routes

from app.request_log import RequestLogMiddleware


app = FastAPI()

# KEEP THIS: one log line per request (status + duration) is what the workspace Monitoring tab charts.
app.add_middleware(RequestLogMiddleware)


@app.get("/")
async def redirect_root_to_docs() -> RedirectResponse:
    return RedirectResponse("/docs")


# A placeholder chain so the template BOOTS. The CLI generates
# `add_routes(app, NotImplemented)`, which raises before the server ever
# listens — replace this echo with your real chain.
echo_chain = RunnableLambda(lambda payload: {"echo": payload})

add_routes(app, echo_chain, path="/echo")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")), access_log=False)
