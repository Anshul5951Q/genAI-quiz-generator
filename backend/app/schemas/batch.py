from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class BatchCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Name of the instructional batch")
    description: str | None = Field(default=None, max_length=1000)
    join_code: str | None = Field(default=None, min_length=4, max_length=32)


class BatchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    is_archived: bool | None = None


class BatchMemberCreate(BaseModel):
    learner_name: str = Field(..., min_length=1, max_length=255)
    learner_email: str = Field(..., pattern=EMAIL_REGEX)
    learner_id: str | None = Field(default=None, max_length=100)


class BatchJoinRequest(BaseModel):
    join_code: str = Field(..., min_length=4, max_length=32)
    learner_name: str = Field(..., min_length=1, max_length=255)
    learner_email: str = Field(..., pattern=EMAIL_REGEX)
    learner_id: str | None = Field(default=None, max_length=100)


class BatchMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    batch_id: str
    learner_name: str
    learner_email: str
    learner_id: str | None = None
    joined_at: datetime


class BatchPublicationBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    quiz_id: str
    quiz_title: str
    access_code: str
    status: str
    time_limit_minutes: int | None = None
    created_at: datetime
    submissions_count: int = 0
    average_score_percentage: float | None = None


class BatchSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    join_code: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    active_publications_count: int = 0


class BatchDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    join_code: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    members: list[BatchMemberResponse] = []
    publications: list[BatchPublicationBrief] = []
