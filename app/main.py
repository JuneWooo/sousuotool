
import os.path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html, get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.config.config import settings


# 自定义swagger 文档
app = FastAPI(title=settings.PROJECT_NAME, description=settings.DESCRIPTION,
              openapi_url=f"{settings.API_V1_STR}/openapi.json", docs_url=None)
# swagger 文档
app.mount("/static", StaticFiles(directory=os.path.join(
    os.path.dirname(__file__), "static")), name="static")


@app.get("/")
def read_main():
    return {"message": "This is your main app"}


# io = gr.Interface(lambda x: "Hello, " + x + "!", "textbox", "textbox")
# app = gr.mount_gradio_app(app, io, path=settings.CUSTOM_PATH)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


app.include_router(api_router, prefix='/api')
