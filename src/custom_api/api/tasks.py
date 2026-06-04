import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from custom_api.utils.tools import initialize_json


class Text(BaseModel):
    """
    Describes the text model
    """

    text_name: str = Field("default", description="the name of the text")
    content: str = Field(
        description="the content of the text",
        min_length=50,
        max_length=5000,
        pattern=r"^[^@#$]*$",
    )


class Task(BaseModel):
    """
    Task: the basetask + the text to process
    """

    text: Text = Field(description="the text object to process")
    task_name: Literal["summary", "sentiment"] = Field(
        "summary", description="The selected task"
    )
    result: str = None

    def full_dump(
        self,
    ):
        res = {"task_name": self.task_name, "result": self.result}
        res.update(self.text.model_dump())

        return res


class TreatedRequest(BaseModel):
    """
    Describes the treated request
    """

    treated_task: Task
    reception_timestamp: datetime
    process_time: timedelta


class TaskStatus(Enum):
    """
    The class describing the state of the task
    """

    PENDING = 0
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3


class TaskRecord(BaseModel):
    """
    Describes the Task sent to the text processor
    """

    task_id: str
    status: TaskStatus
    task: Task
    created_at: datetime
    completed_at: datetime = None
    username: str

    def get_info(
        self,
    ):
        return self.task_id, self.status


current_dir = Path(__file__).parent
TASKRECORDS_DB_PATH = current_dir / "taskrecords_db.json"


class TaskStore(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    records: Optional[dict[str, TaskRecord]] = None
    task_references: list[asyncio.Task] = []

    def load_records(self, path: str = TASKRECORDS_DB_PATH):

        if self.records is None:
            try:
                with open(path, "r") as f:
                    taskrecords_db = json.load(f)
            except OSError:
                initialize_json(path)
                with open(path, "r") as f:
                    taskrecords_db = json.load(f)

            self.records = taskrecords_db

        return self

    def save_records(self, path: str = TASKRECORDS_DB_PATH):

        if self.records:
            with open(path, "w") as f:
                json.dump(self.records, f)

    def set_record(self, task_id: str, task_record: TaskRecord):
        self.records[task_id] = task_record

    def add_reference(self, task_ref: asyncio.Task):
        self.task_references.append(task_ref)
