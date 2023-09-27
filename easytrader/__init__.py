# -*- coding: utf-8 -*-
import urllib3

from . import exceptions
from .api import use, follower
from .log import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__version__ = "0.23.0"
__author__ = "shidenggui"
