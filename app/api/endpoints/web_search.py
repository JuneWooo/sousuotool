from fastapi import APIRouter
from typing import List
from app.service.web_search import web_search
from app.api.resp import RESPModel, resp, RespStatus
from app.schemas.search_schema import SearchData

router = APIRouter()


@router.get("/web_delta_search", response_model=RESPModel[List[SearchData]])
def api_web_search(query: str, num: int = 5):
    data = web_search.delta_search(query, num)

    if data:
        return resp(status_code=RespStatus.success, msg="success", data=data)
    else:
        return resp(status_code=RespStatus.error, msg="error", data=data)


@router.get("/web_full_search", response_model=RESPModel[List[SearchData]])
def api_full_search(query: str, num: int = 5):
    data = web_search.full_search(query, num)
    if data:
        return resp(status_code=RespStatus.success, msg="success", data=data)
    else:
        return resp(status_code=RespStatus.error, msg="error", data=data)


@router.get("/web_url_search", response_model=RESPModel[List[SearchData]])
def api_url_search(query: str):
    data = web_search.url_search(query)
    if data:
        return resp(status_code=RespStatus.success, msg="success", data=data)
    else:
        return resp(status_code=RespStatus.error, msg="error", data=data)
