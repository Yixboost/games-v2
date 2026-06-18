from fastapi import Request

from core.templates import base_context, templates


async def custom_404_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context=base_context(),
        status_code=404,
    )


HTTP_EXCEPTIONS = {404: custom_404_exception_handler}
