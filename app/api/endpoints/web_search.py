
from fastapi import APIRouter
from typing import List
from app.service.web_search import web_search
from app.api.resp import *
from app.schemas.search_schema import SearchData

router = APIRouter()


@router.post("/web_delta_search", response_model=RESPModel[List[SearchData]])
def api_web_search(message: str):

    data = web_search.delta_search(message)

    if data:
        return resp(status_code=RespStatus.success, msg="success", data=data)
    else:
        return resp(status_code=RespStatus.error, msg="error", data=data)


@router.post("/web_full_search", response_model=RESPModel[List[SearchData]])
def api_web_search(message: str):

    data = web_search.full_search(message)
    if data:
        return resp(status_code=RespStatus.success, msg="success", data=data)
    else:
        return resp(status_code=RespStatus.error, msg="error", data=data)


@router.post("/web_url_search", response_model=RESPModel[List[SearchData]])
def api_web_search(message: str):

    data = web_search.url_search(message)
    if data:
        return resp(status_code=RespStatus.success, msg="success", data=data)
    else:
        return resp(status_code=RespStatus.error, msg="error", data=data)