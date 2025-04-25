# src/my_types.py
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class BrowserInfo:
    user_id: int
    user_data_dir: str
    user_agent: str
    headless: str


@dataclass
class ActionInfo:
    action_name: str
    images_path: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


@dataclass
class TaskInfo:
    browser_info: BrowserInfo
    action: ActionInfo


# @dataclass
# class Action
