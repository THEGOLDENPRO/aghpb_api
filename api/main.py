from typing import List, Tuple, Dict # DON'T YOU DARE PUT THIS UNDER TYPE_CHECKING!!! I'm warning you!

import os
from thefuzz import fuzz
from datetime import datetime
from email.utils import formatdate

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from meow_inator_5000.woutews import nya_service

from .info import InfoData
from .book import Book, BookData
from . import errors, __version__
from .anime_girls import ProgrammingBooks, CategoryNotFound
from .constants import RANDOM_BOOK_RATE_LIMIT, GET_BOOK_RATE_LIMIT

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

<br>

Rate limiting applies to the ``/random`` and ``/get`` endpoints. Check out the rate limits [over here](https://github.com/THEGOLDENPRO/aghpb_api/wiki#rate-limiting).
"""

limiter = Limiter(key_func=get_remote_address, headers_enabled = True)
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

    root_path = ROOT_PATH
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, errors.rate_limit_handler)
app.include_router(nya_service.router)

@app.get(
    "/",
    name = "Takes you to these docs.",
    tags = ["misc"]
)
async def root():
    """Redirects you to this documentation page."""
    return RedirectResponse(f"{ROOT_PATH}/docs")


get_book_cache: Dict[str, float] = {}
programming_books = ProgrammingBooks()

@app.get(
    "/info",
    name = "Info about the current instance.",
    tags = ["other"]
)
async def info() -> InfoData:
    """Returns repository information like book count and etc."""
    return {
        "api_version": __version__,
        "book_count": len(programming_books.books),
        "repo_hash": programming_books.repo_hash,
        "repo_last_updated": str(programming_books.repo_last_updated)
    }


@app.get(
    "/random",
    name = "Get a random Book",
    tags = ["books"],
    response_class = FileResponse,
    responses = {
        200: {
            "content": {
                "image/png": {},
                "image/jpeg": {}
            },
            "description": "Returned an anime girl holding a programming book successfully. 😁",
        },
        404: {
            "model": errors.CategoryNotFound, 
            "description": "The category was not Found."
        },
        429: {
            "model": errors.RateLimited,
            "description": "Rate limit exceeded!"
        }
    },
)
@limiter.limit(f"{RANDOM_BOOK_RATE_LIMIT}/second")
async def random(request: Request, category: str = None) -> FileResponse:
    """Returns a random book."""
    if category is None:
        category = programming_books.random_category()

    try:
        book = programming_books.random_book(category)

    except CategoryNotFound as e:
        return JSONResponse(
            status_code = 404, 
            content = {
                "error": e.__class__.__name__,
                "message": e.msg
            }
        )

    return book.to_file_response()


@app.get(
    "/categories",
    name = "All Available Categories",
    tags = ["books"]
)
async def categories() -> List[str]:
    """Returns a list of all available categories."""
    return programming_books.categories


@app.get(
    "/search",
    name = "Query for books.",
    tags = ["books"]
)
async def search(
    query: str, 
    category: str = None, 
    limit: int = Query(ge = 1, default = 50)
) -> List[BookData]:
    """Returns list of book objects."""
    books: List[Tuple[int, Book]] = []

    for book in programming_books.books:
        if len(books) == limit:
            break

        if category is not None and not category.lower() == book.category.lower():
            continue

        name_match = fuzz.partial_ratio(book.name.lower(), query.lower())

        if name_match > 70:
            books.append((name_match, book))

    books.sort(key = lambda x: x[0], reverse = True) # Sort in order of highest match.

    return [
        book[1].to_dict() for book in books
    ]


@app.get(
    "/get/id/{search_id}",
    name = "Allows you to get a book by search id.",
    tags = ["books"],
    response_class = FileResponse,
    responses = {
        200: {
            "content": {
                "image/png": {},
                "image/jpeg": {}
            },
            "description": "Returned an anime girl holding a programming book successfully. 😁",
        },
        404: {
            "model": errors.BookNotFound, 
            "description": "The book was not Found."
        },
        429: {
            "model": errors.RateLimited,
            "description": "Rate Limit exceeded"
        }
    },
)
@limiter.limit(f"{GET_BOOK_RATE_LIMIT}/second")
async def get_id(request: Request, search_id: str) -> FileResponse:
    """Returns the book found."""
    expires_timestamp = get_book_cache.get(search_id, 0)

    if datetime.now().timestamp() > expires_timestamp:
        timestamp_to_set = datetime.now().timestamp() + 60 # 60 seconds until this book expires. 
        # (NOTE: If you update the git repo it may take a literal minute for books to refresh, depending on how your master server caches.)

        expires_timestamp = timestamp_to_set
        get_book_cache[search_id] = timestamp_to_set

    for book in programming_books.books:

        if book.search_id == search_id:
            return book.to_file_response(
                0 if expires_timestamp is None else formatdate(expires_timestamp, usegmt = True)
            )

    return JSONResponse(
        status_code = 404, 
        content = {
            "error": "BookNotFound",
            "message": f"We couldn't find a book with search id '{search_id}'!"
        }
    )