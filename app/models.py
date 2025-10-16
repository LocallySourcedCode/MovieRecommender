from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, UniqueConstraint


class User(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("email"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    password_hash: str


# ---- Group recommender domain models ----
class Group(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("code"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    host_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    code: str = Field(index=True, description="Short unique join code")
    phase: str = Field(default="setup", index=True, description="setup|genre_nomination|genre_voting|movie_selection|finalized")
    veto_enabled: Optional[bool] = Field(default=None, description="None until decided, then True/False")
    veto_decided_at: Optional[datetime] = Field(default=None)
    current_movie_id: Optional[int] = Field(default=None, foreign_key="moviecandidate.id")
    winner_movie_id: Optional[int] = Field(default=None, foreign_key="moviecandidate.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class Participant(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_participant_group_user"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    display_name: str
    is_host: bool = Field(default=False, index=True)
    has_veto: bool = Field(default=False)
    veto_used: bool = Field(default=False)
    streaming_services_json: Optional[str] = Field(default=None, description="JSON array of streaming providers for this participant")


class Invite(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("code"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", index=True)
    code: str = Field(index=True)
    expires_at: Optional[datetime] = Field(default=None, index=True)
    created_by_participant_id: int = Field(foreign_key="participant.id")


class SettingVote(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("group_id", "participant_id", "key"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", index=True)
    participant_id: int = Field(foreign_key="participant.id", index=True)
    key: str = Field(index=True)
    value_bool: Optional[bool] = Field(default=None)


class GenreNomination(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("group_id", "participant_id", "genre"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", index=True)
    participant_id: int = Field(foreign_key="participant.id", index=True)
    genre: str = Field(index=True)


class GenreVote(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("group_id", "participant_id", "genre"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", index=True)
    participant_id: int = Field(foreign_key="participant.id", index=True)
    genre: str = Field(index=True)
    value: int = Field(default=1)


class MovieCandidate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", index=True)
    title: str
    source: str = Field(default="demo", index=True)
    metadata_json: Optional[str] = Field(default=None)
    disqualified: bool = Field(default=False, index=True)


class MovieVote(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("group_id", "participant_id"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", index=True)
    participant_id: int = Field(foreign_key="participant.id", index=True)
    movie_id: int = Field(foreign_key="moviecandidate.id", index=True)
    value: int = Field(default=1)


class GenreFinalized(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("group_id", "genre"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", index=True)
    genre: str = Field(index=True)
