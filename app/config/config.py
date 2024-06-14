# -*- coding:utf-8 -*-
"""
@file: config.py
@author: June
@date: 2024/3/1
@IDE: vscode
"""
from pydantic_settings import BaseSettings


class Setting(BaseSettings):
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    PROJECT_NAME: str = "Web Search"
    DESCRIPTION: str = "search"

    BAIDU_URL: str = "https://www.baidu.com/"
    BING_URL: str = "https://cn.bing.com/"

    # api
    API_V1_STR: str = "/api"
    IS_DEV: bool

    # log
    LOG_DIR: str = "logs/crawl_data{time}.log"
    LOG_LEVEL: str


settings = Setting()
