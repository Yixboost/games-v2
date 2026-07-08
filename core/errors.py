from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import Response

from core.templates import base_context, templates


async def custom_404_exception_handler(request: Request, exc: HTTPException):
    context = base_context(request)
    context["error"] = {
        "code": 404,
        "description": "The page you requested could not be found.",
    }

    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context=context,
        status_code=404,
    )


async def custom_http_exception_handler(request: Request, exc: HTTPException):
    context = base_context(request)
    context["error"] = {
        "code": exc.status_code,
        "description": exc.detail
        if isinstance(exc.detail, str)
        else "An unexpected error occurred.",
    }

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context=context,
        status_code=exc.status_code,
    )


async def custom_exception_handler(request: Request, exc: Exception):
    context = base_context(request)
    context["error"] = {
        "code": 500,
        "description": "An internal server error occurred.",
    }

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context=context,
        status_code=500,
    )


HTTP_EXCEPTIONS = {
    404: custom_404_exception_handler,
    HTTPException: custom_http_exception_handler,
    Exception: custom_exception_handler,
}