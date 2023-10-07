# -*- coding: utf-8 -*-
import logging
# 创建日志记录器
logger = logging.getLogger("easytrader")
# 记录日志级别
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
logger.propagate = False
# 创建格式化程序
fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(filename)s %(lineno)s: %(message)s"
)
ch = logging.StreamHandler()
# 将格式化程序应用到处理程序
ch.setFormatter(fmt)

file_hander = logging.FileHandler('app.log')
file_hander.setLevel(logging.FATAL)
file_hander.setFormatter(fmt)

logger.handlers.append(ch)
logger.handlers.append(file_hander)
