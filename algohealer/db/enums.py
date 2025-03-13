import os
from enum import Enum
from typing import List

from pydantic import BaseModel


class Category(str, Enum):
    travel = "travel"
    food = "food"
    health = "health"
    nature = "nature"
    technology = "technology"
    finance = "finance"


CATEGORIES = [category.value for category in list(Category)]


class Settings(BaseModel):
    headless: bool = True
    channel: str = "chrome"
    user_data_dir: str = f"C:/Users/{os.getenv('USERNAME', 'TEMP')}/AppData/Local/Google/Chrome/User Data"
    interests: List[Category] = [CATEGORIES]
