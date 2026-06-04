import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from pandas import DataFrame, to_datetime, to_timedelta
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from custom_api.api.tasks import TreatedRequest
from custom_api.utils.tools import initialize_json


class User(BaseModel):
    username: str
    hashed_password: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserRequests(BaseModel):
    user: User
    treated_requests: List[TreatedRequest]
    treated_requests_df: DataFrame

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("treated_requests", mode="before")
    def validate_request(cls, value):
        if isinstance(value, list):
            return [TreatedRequest.model_validate(item) for item in value]

    @field_validator("treated_requests_df", mode="before")
    def validate_dataframe(cls, value):

        if isinstance(value, list):
            df = DataFrame(value)

            if "reception_time" in df.columns:
                df["reception_time"] = to_datetime(df["reception_time"])

            if "process_time" in df.columns:
                df["process_time"] = to_timedelta(df["process_time"])

            return df

        elif not isinstance(value, DataFrame):
            raise ValueError("treated_requests_df should be a pandas DataFrame object")
        else:
            return value

    @field_serializer("treated_requests_df", when_used="json")
    def serialize_df(self, treated_requests_df: DataFrame):
        return treated_requests_df.to_dict(orient="records")

    @classmethod
    def create_new_user_requests(cls, user: User, tr: TreatedRequest):
        """
        Instantiate a new UserRequests object from a single request
        """

        record = {
            "reception_time": tr.reception_timestamp,
            "process_time": tr.process_time,
        }
        record.update(tr.treated_task.full_dump())

        # Temporary fix for pydantic
        tr_json = tr.model_dump_json()
        tr = TreatedRequest.model_validate_json(tr_json)

        return cls(
            user=user, treated_requests=[tr], treated_requests_df=DataFrame([record])
        )

    def add_new_request(self, tr: TreatedRequest) -> None:
        self.treated_requests.append(tr)
        record = {
            "reception_time": tr.reception_timestamp,
            "process_time": tr.process_time,
        }
        record.update(tr.treated_task.full_dump())
        self.treated_requests_df.loc[len(self.treated_requests_df)] = record

    def is_request_allowed(self, max_req_per_min: int) -> bool:
        now = datetime.now()
        period = timedelta(minutes=1)
        period_start = now - period
        return (
            len(
                self.treated_requests_df[
                    self.treated_requests_df["reception_time"] >= period_start
                ]
            )
            < max_req_per_min
        )


current_dir = Path(__file__).parent
JSON_PATH_USERS = current_dir / "users.json"
JSON_PATH_USERS_REQUESTS = current_dir / "users_requests.json"


def load_user_db() -> dict:

    try:
        with open(JSON_PATH_USERS, "r") as f:
            user_db = json.load(f)
    except OSError:
        initialize_json(JSON_PATH_USERS)
        with open(JSON_PATH_USERS, "r") as f:
            user_db = json.load(f)

    return user_db


def update_user_db(user_db: dict, user: User):
    user_db[user.username] = user.model_dump_json()

    with open(JSON_PATH_USERS, "w") as f:
        json.dump(user_db, f)


# USER REQUESTS #


def load_users_requests_db() -> dict[str, UserRequests]:

    try:
        with open(JSON_PATH_USERS_REQUESTS, "r") as f:
            users_requests_db = json.load(f)
    except OSError:
        initialize_json(JSON_PATH_USERS_REQUESTS)
        with open(JSON_PATH_USERS_REQUESTS, "r") as f:
            users_requests_db = json.load(f)

    return users_requests_db


def update_users_requests_db(users_requests_db: dict):

    with open(JSON_PATH_USERS_REQUESTS, "w") as f:
        json.dump(users_requests_db, f)
