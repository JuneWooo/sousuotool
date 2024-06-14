# -*- coding:utf-8 -*-
from fastapi import APIRouter
from app.api.endpoints import web_search


api_router = APIRouter()
api_router.include_router(web_search.router,
                          prefix="/tali", tags=["tali"])
