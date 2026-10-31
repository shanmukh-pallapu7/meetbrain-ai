from pydantic import BaseModel, Field, field_validator


class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    deadline: str | None = None


class MeetingReport(BaseModel):
    title: str = Field(min_length=1)
    summary: str
    key_decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    follow_up_email: str


@field_validator("title")
@classmethod
def title_must_not_be_blank(cls, value: str) -> str:
    if not value.strip():
        raise ValueError("Meeting title must not be blank")
    return value.strip()
