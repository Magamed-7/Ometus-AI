from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.code = code
        self.message = message
        self.status_code = status_code


def error_response(code: str, message: str, status_code: int, fields: list | None = None):
    error = {"code": code, "message": message, "status": status_code}

    # список полей отдаём отдельным ключом, а не только в тексте: интерфейс трёхъязычный
    # и показывает свой перевод по коду, но подставить в него имена полей может
    if fields:
        error["fields"] = fields

    return JSONResponse(status_code=status_code, content={"error": error})


async def app_error_handler(request: Request, exc: AppError):
    return error_response(exc.code, exc.message, exc.status_code)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return error_response("HTTP_ERROR", str(exc.detail), exc.status_code)


def failed_fields(exc: RequestValidationError):
    names = []

    for error in exc.errors():
        # loc это ("body", "email") или ("query", "limit"); первый элемент — источник,
        # он пользователю ничего не говорит, а вот имя поля говорит
        parts = [str(part) for part in error.get("loc", ())[1:] if not isinstance(part, int)]

        if parts and parts[-1] not in names:
            names.append(parts[-1])

    return names


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    # без списка полей форма показывает «проверьте введённые данные» и человек гадает,
    # что именно не так: поймано на создании врача с почтой в зарезервированном домене
    fields = failed_fields(exc)
    message = "Некорректные данные запроса"

    if fields:
        message = f"{message}: {', '.join(fields)}"

    return error_response(
        "VALIDATION_ERROR", message, status.HTTP_422_UNPROCESSABLE_CONTENT, fields
    )


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
