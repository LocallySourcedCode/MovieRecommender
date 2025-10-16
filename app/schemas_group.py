from typing import Optional, List
from pydantic import BaseModel, Field


# ---- Request models ----
class GroupCreateGuest(BaseModel):
    display_name: str = Field(min_length=1, max_length=60)
    streaming_services: Optional[list[str]] = None


class GroupJoinGuest(BaseModel):
    display_name: str = Field(min_length=1, max_length=60)
    streaming_services: Optional[list[str]] = None


class GenresNominateIn(BaseModel):
    genres: List[str] = Field(min_length=1, max_length=2)


class GenreVoteIn(BaseModel):
    genre: str


# ---- Response models ----
class ParticipantOut(BaseModel):
    id: int
    display_name: str
    is_host: bool
    has_veto: bool
    veto_used: bool
    streaming_services: Optional[list[str]] = None


class GroupOut(BaseModel):
    id: int
    code: str
    phase: str
    veto_enabled: Optional[bool] = None
    participants: List[ParticipantOut] = Field(default_factory=list)


class GroupCreateResponse(BaseModel):
    group: GroupOut
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"


class GroupJoinResponse(BaseModel):
    group: GroupOut
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
