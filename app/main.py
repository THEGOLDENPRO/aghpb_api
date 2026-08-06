from typing import Annotated

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse

from . import __version__
from .info import Info
from .routers import books
from .errors import APIError
from .repository import ProgrammingBooks
from .dependencies import get_programming_books

ROOT_PATH = os.environ.get("ROOT_PATH", "") # Like: /aghpb/v1

TAGS_METADATA = [
    {
        "name": "books",
        "description": "The main endpoints that allow you to get books." \
            "\n\n**All books come with extra info via headers like: ``Book-Name``, ``Book-Category``, ``Book-Date-Added``**",
    },
    {
        "name": "other",
        "description": "Other endpoints."
    },
    {
        "name": "misc",
        "description": "Non-important endpoints."
    }
]

DESCRIPTION = """
<div align="center">

  <img src="https://raw.githubusercontent.com/THEGOLDENPRO/aghpb_api/main/assets/logo.png" alt="Logo" width="180">

  Behold the **anime girls holding programming books** API. ✴️

  This is a ✨ feature rich 🌟 [open source](https://github.com/THEGOLDENPRO/aghpb_api) API I made for the anime girls holding programming books [github repo](https://github.com/cat-milk/Anime-Girls-Holding-Programming-Books) because I was bored.

  🐞 Report bugs [over here](https://github.com/THEGOLDENPRO/aghpb_api/issues).

</div>
""" + books.RATE_LIMITING_DESCRIPTION_MESSAGE

@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = ProgrammingBooks()

    repository.update_repo()
    repository.parse_books()

    app.state.repository = repository

    yield

app = FastAPI(
    title = "aghpb API",
    description = DESCRIPTION,
    license_info = {
        "name": "Apache 2.0",
        "identifier": "MIT",
    },
    openapi_tags = TAGS_METADATA,
    swagger_favicon_url = "https://raw.githubusercontent.com/THEGOLDENPRO/aghpb_api/main/assets/logo.png",
    version = f"v{__version__}",
    lifespan = lifespan,

    root_path = ROOT_PATH
)
app.include_router(books.router)

@app.get(
    "/",
    name = "Takes you to these docs.",
    tags = ["misc"]
)
async def root():
    """Redirects you to this documentation page."""
    return RedirectResponse(f"{ROOT_PATH}/docs")

@app.get(
    "/info",
    name = "Info about the current instance.",
    tags = ["other"]
)
async def info(programming_books: Annotated[ProgrammingBooks, Depends(get_programming_books)]) -> Info:
    """Returns repository information like book count and etc."""
    return Info(
        api_version = __version__,
        book_count = programming_books.get_book_count(),
        repo_hash = programming_books.get_repo_hash(),
        repo_last_updated = str(programming_books.get_repo_last_updated())
    )

@app.exception_handler(APIError)
async def api_exception_handler(request: Request, exception: APIError):
    return JSONResponse(
        status_code = exception.status_code,
        content = {
            "error": exception.error,
            "message": exception.message
        }
    )