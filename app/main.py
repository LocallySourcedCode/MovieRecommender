from contextlib import asynccontextmanager
import json
from app.services.recommendations import get_next_candidate, get_candidate_queue
from app.security import (
    hash_password,
    verify_password,
    create_token,
    JWT_SECRET,
    JWT_ALG,
    parse_subject,
    create_participant_token,
)
from app.schemas_group import (
    GroupCreateGuest,
    GroupCreateResponse,
    GroupJoinGuest,
    GroupJoinResponse,
    GroupOut,
    ParticipantOut,
    GenresNominateIn,
    GenreVoteIn,
)
from app.schemas import UserCreate, UserRead, Token
from app.models import User, Group, Participant, MovieCandidate, MovieVote, GenreNomination, GenreVote, GenreFinalized
from app.db import get_session, init_db, ensure_tables
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, HTTPException
from collections import Counter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import random
import string
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on app startup using modern lifespan API (on_event is deprecated)
    init_db()
    yield

app = FastAPI(title="MovieRecommender API", lifespan=lifespan)

# CORS for local React dev server (Vite on port 5173). Safe for dev; tighten for prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_optional = OAuth2PasswordBearer(
    tokenUrl="/auth/login", auto_error=False)


@app.post("/auth/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, session: Session = Depends(get_session)):
    # ensure tables exist for the current connection (important for in-memory test DB)
    ensure_tables(session)
    # password policy: min 8, max 32 characters
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=400, detail="Password too short (min 8 characters)")
    if len(payload.password) > 32:
        raise HTTPException(
            status_code=400, detail="Password too long (max 32 characters)")
    existing = session.exec(select(User).where(
        User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email,
                password_hash=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserRead(id=user.id, email=user.email)


@app.post("/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    # ensure tables exist for the current connection (important for in-memory test DB)
    ensure_tables(session)
    user = session.exec(select(User).where(
        User.email == form.username)).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(str(user.id))
    return Token(access_token=token)


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    # ensure tables exist for the current connection (important for in-memory test DB)
    ensure_tables(session)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        uid = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.get("/me", response_model=UserRead)
def me(current: User = Depends(get_current_user)):
    return UserRead(id=current.id, email=current.email)


# ---- Mixed identity helpers and endpoints ----

def _generate_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def _services_list(p: Participant) -> Optional[list[str]]:
    try:
        import json
        return json.loads(p.streaming_services_json) if p.streaming_services_json else None
    except Exception:
        return None


def _serialize_group(session: Session, group: Group) -> GroupOut:
    participants = session.exec(select(Participant).where(
        Participant.group_id == group.id)).all()
    return GroupOut(
        id=group.id,
        code=group.code,
        phase=group.phase,
        veto_enabled=group.veto_enabled,
        participants=[
            ParticipantOut(
                id=p.id,
                display_name=p.display_name,
                is_host=p.is_host,
                has_veto=p.has_veto,
                veto_used=p.veto_used,
                streaming_services=_services_list(p),
            )
            for p in participants
        ],
    )


def _resolve_principal(session: Session, token: Optional[str]):
    """Return (kind, obj) or (None, None) if no token provided."""
    if not token:
        return None, None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        sub = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    kind, pid = parse_subject(sub)
    if kind == "user":
        user = session.get(User, pid)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return "user", user
    elif kind == "participant":
        participant = session.get(Participant, pid)
        if not participant:
            raise HTTPException(
                status_code=401, detail="Participant not found")
        return "participant", participant
    else:
        raise HTTPException(status_code=401, detail="Invalid token subject")


@app.get("/whoami")
def whoami(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    ensure_tables(session)
    kind, obj = _resolve_principal(session, token)
    if kind == "user":
        return {"kind": "user", "id": obj.id, "email": obj.email}
    elif kind == "participant":
        return {"kind": "participant", "id": obj.id, "group_id": obj.group_id, "display_name": obj.display_name, "is_host": bool(getattr(obj, "is_host", False))}


@app.get("/config")
def config():
    """Minimal config introspection for debugging TMDb integration."""
    tmdb_configured = bool(os.getenv("TMDB_READ_TOKEN")
                           or os.getenv("TMDB_API_KEY"))
    region = os.getenv("TMDB_REGION", "US")
    return {"tmdb_configured": tmdb_configured, "tmdb_region": region}


def _is_group_active(g: Group) -> bool:
    return (g.phase or "setup") != "finalized"


def _find_active_group_for_user(session: Session, user_id: int) -> Optional[Group]:
    # Find any non-finalized group where this user is a participant
    rows = session.exec(select(Participant).where(
        Participant.user_id == user_id)).all()
    for p in rows:
        grp = session.get(Group, p.group_id)
        if grp and _is_group_active(grp):
            return grp
    return None


def _disband_group(session: Session, group: Group):
    # Delete all related rows to fully remove the group
    # Movie votes
    for mv in session.exec(select(MovieVote).where(MovieVote.group_id == group.id)).all():
        session.delete(mv)
    # Movie candidates
    for mc in session.exec(select(MovieCandidate).where(MovieCandidate.group_id == group.id)).all():
        session.delete(mc)
    # Genre votes/nom
    for gv in session.exec(select(GenreVote).where(GenreVote.group_id == group.id)).all():
        session.delete(gv)
    for gn in session.exec(select(GenreNomination).where(GenreNomination.group_id == group.id)).all():
        session.delete(gn)
    # Finalized genres
    for gf in session.exec(select(GenreFinalized).where(GenreFinalized.group_id == group.id)).all():
        session.delete(gf)
    # Participants
    for p in session.exec(select(Participant).where(Participant.group_id == group.id)).all():
        session.delete(p)
    # Group last
    session.delete(group)
    session.commit()


@app.post("/groups/leave")
def leave_current_group(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    """Leave the current active group. If caller is the host, disband the group.
    Works for both participant and user tokens.
    """
    ensure_tables(session)
    kind, principal = _resolve_principal(session, token)
    if kind == "participant":
        participant: Participant = principal
        group = session.get(Group, participant.group_id)
        if not group or not _is_group_active(group):
            raise HTTPException(
                status_code=404, detail="No active group to leave")
        code = group.code
        if participant.is_host:
            _disband_group(session, group)
            return {"ok": True, "action": "disbanded", "group_code": code}
        else:
            session.delete(participant)
            session.commit()
            return {"ok": True, "action": "left", "group_code": code}
    elif kind == "user":
        group = _find_active_group_for_user(session, principal.id)
        if not group:
            raise HTTPException(
                status_code=404, detail="No active group to leave")
        code = group.code
        p = session.exec(
            select(Participant).where(Participant.group_id ==
                                      group.id, Participant.user_id == principal.id)
        ).first()
        if p and p.is_host:
            _disband_group(session, group)
            return {"ok": True, "action": "disbanded", "group_code": code}
        elif p:
            session.delete(p)
            session.commit()
            return {"ok": True, "action": "left", "group_code": code}
        else:
            # No participant row, nothing to do
            raise HTTPException(
                status_code=404, detail="No active group to leave")
    else:
        raise HTTPException(status_code=401, detail="Invalid token subject")


@app.post("/groups", response_model=GroupCreateResponse)
def create_group(
    guest_payload: Optional[GroupCreateGuest] = None,
    token: Optional[str] = Depends(oauth2_optional),
    session: Session = Depends(get_session),
):
    """Create a group as a signed-in user (if token provided) or as a guest.
    For guests, a participant token is issued and returned.
    """
    ensure_tables(session)

    # Generate unique join code
    code = _generate_code()
    # ensure uniqueness
    while session.exec(select(Group).where(Group.code == code)).first() is not None:
        code = _generate_code()

    if token:
        kind, principal = _resolve_principal(session, token)
        if kind == "participant":
            # Participant token represents an existing group membership; require leaving first
            grp = session.get(Group, principal.group_id)
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "participant_in_active_group",
                    "message": "You are already in a group. Leave or disband before creating a new group.",
                    "group_code": grp.code if grp else None,
                    "role": "host" if getattr(principal, "is_host", False) else "member",
                },
            )
        if kind != "user":
            raise HTTPException(
                status_code=401, detail="Invalid token subject")
        # Enforce single active membership for users
        existing_group = _find_active_group_for_user(session, principal.id)
        if existing_group:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "already_in_active_group",
                    "message": "You are already in another active group. Leave or disband it first.",
                    "group_code": existing_group.code,
                },
            )
        # Create group with host_user_id
        group = Group(code=code, host_user_id=principal.id,
                      phase="genre_nomination")
        session.add(group)
        session.commit()
        session.refresh(group)
        # Create participant for host
        display = principal.email.split("@")[0]
        host = Participant(group_id=group.id, user_id=principal.id,
                           display_name=display, is_host=True)
        session.add(host)
        session.commit()
        group_out = _serialize_group(session, group)
        return GroupCreateResponse(group=group_out)
    else:
        # Guest path requires display_name
        if guest_payload is None or not guest_payload.display_name:
            raise HTTPException(
                status_code=422, detail="display_name is required for guests")
        group = Group(code=code, host_user_id=None, phase="genre_nomination")
        session.add(group)
        session.commit()
        session.refresh(group)
        import json as _json
        services = None
        if guest_payload.streaming_services:
            try:
                services = _json.dumps(guest_payload.streaming_services)
            except Exception:
                services = None
        host = Participant(
            group_id=group.id,
            user_id=None,
            display_name=guest_payload.display_name,
            is_host=True,
            streaming_services_json=services,
        )
        session.add(host)
        session.commit()
        session.refresh(host)
        token_value = create_participant_token(host.id)
        group_out = _serialize_group(session, group)
        return GroupCreateResponse(group=group_out, access_token=token_value, token_type="bearer")


@app.post("/groups/{code}/join", response_model=GroupJoinResponse)
def join_group(
    code: str,
    guest_payload: Optional[GroupJoinGuest] = None,
    token: Optional[str] = Depends(oauth2_optional),
    session: Session = Depends(get_session),
):
    ensure_tables(session)
    group = session.exec(select(Group).where(Group.code == code)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if token:
        kind, principal = _resolve_principal(session, token)
        if kind == "user":
            # Enforce single active membership: if user is in another active group, require leaving first
            other_group = _find_active_group_for_user(session, principal.id)
            if other_group and other_group.id != group.id:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "already_in_active_group",
                        "message": "You are already in another active group. Leave it before joining a new one.",
                        "group_code": other_group.code,
                    },
                )
            # idempotent join for users
            existing = session.exec(
                select(Participant).where(Participant.group_id ==
                                          group.id, Participant.user_id == principal.id)
            ).first()
            if not existing:
                display = principal.email.split("@")[0]
                p = Participant(group_id=group.id, user_id=principal.id,
                                display_name=display, is_host=False)
                session.add(p)
                session.commit()
            group_out = _serialize_group(session, group)
            return GroupJoinResponse(group=group_out)
        elif kind == "participant":
            # Participant tokens are tied to a specific group via their record
            participant = principal
            if participant.group_id != group.id:
                raise HTTPException(
                    status_code=403, detail="Participant token belongs to a different group")
            group_out = _serialize_group(session, group)
            return GroupJoinResponse(group=group_out)
        else:
            raise HTTPException(
                status_code=401, detail="Invalid token subject")
    else:
        # Guest join requires display_name
        if guest_payload is None or not guest_payload.display_name:
            raise HTTPException(
                status_code=422, detail="display_name is required for guests")
        import json as _json
        services = None
        if guest_payload.streaming_services:
            try:
                services = _json.dumps(guest_payload.streaming_services)
            except Exception:
                services = None
        p = Participant(
            group_id=group.id,
            user_id=None,
            display_name=guest_payload.display_name,
            is_host=False,
            streaming_services_json=services,
        )
        session.add(p)
        session.commit()
        session.refresh(p)
        token_value = create_participant_token(p.id)
        group_out = _serialize_group(session, group)
        return GroupJoinResponse(group=group_out, access_token=token_value, token_type="bearer")


# ---- Swipe flow endpoints ----

def _shared_providers(session: Session, group_id: int) -> Optional[set[str]]:
    participants = session.exec(select(Participant).where(
        Participant.group_id == group_id)).all()
    provider_sets = []
    for p in participants:
        if p.streaming_services_json:
            try:
                lst = json.loads(p.streaming_services_json)
                if lst:
                    provider_sets.append(set(map(str.lower, lst)))
            except Exception:
                continue
    if not provider_sets:
        return None
    shared = set.intersection(*provider_sets)
    return shared if shared else None


def _require_member(session: Session, group: Group, token: str) -> Participant:
    kind, obj = _resolve_principal(session, token)
    if kind == "participant":
        if obj.group_id != group.id:
            raise HTTPException(
                status_code=403, detail="Participant token belongs to a different group")
        return obj
    elif kind == "user":
        p = session.exec(
            select(Participant).where(Participant.group_id ==
                                      group.id, Participant.user_id == obj.id)
        ).first()
        if not p:
            raise HTTPException(
                status_code=403, detail="You are not a member of this group")
        return p
    else:
        raise HTTPException(status_code=401, detail="Invalid token subject")


def _candidate_payload(movie: MovieCandidate) -> dict:
    meta = {}
    if movie.metadata_json:
        try:
            meta = json.loads(movie.metadata_json)
        except Exception:
            meta = {}
    return {
        "id": movie.id,
        "title": movie.title,
        "source": movie.source,
        **meta,
    }


@app.get("/groups/{code}/movies/current")
def get_current_movie(code: str, token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    ensure_tables(session)
    group = session.exec(select(Group).where(Group.code == code)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    _ = _require_member(session, group, token)

    # Purge any non-TMDb candidates if TMDb is configured to guarantee no demo leftovers
    tmdb_configured = bool(os.getenv("TMDB_READ_TOKEN")
                           or os.getenv("TMDB_API_KEY"))
    if tmdb_configured:
        existing_cands = session.exec(select(MovieCandidate).where(
            MovieCandidate.group_id == group.id)).all()
        purged_ids = []
        for mc in existing_cands:
            if (mc.source or "").lower() != "tmdb":
                purged_ids.append(mc.id)
                session.delete(mc)
        if purged_ids:
            # remove votes tied to purged candidates and reset current if needed
            votes = session.exec(select(MovieVote).where(
                MovieVote.group_id == group.id)).all()
            for v in votes:
                if v.movie_id in purged_ids:
                    session.delete(v)
            if group.current_movie_id in purged_ids:
                group.current_movie_id = None
            session.add(group)
            session.commit()

    # Note: movies can be previewed even before movie_selection; finalized genre filter applies when available.

    # If current exists and is not disqualified, return it
    if group.current_movie_id:
        current = session.get(MovieCandidate, group.current_movie_id)
        if current and not current.disqualified:
            # If genres are finalized and TMDb is configured, only accept a queued TMDb candidate
            finalized_now = _finalized_genres(session, group.id)
            if finalized_now and tmdb_configured:
                try:
                    meta = json.loads(current.metadata_json or "{}")
                except Exception:
                    meta = {}
                reason = meta.get("reason") if isinstance(meta, dict) else None
                if not (isinstance(reason, str) and reason.startswith("tmdb:queue")):
                    # Invalidate current so we can rebuild
                    group.current_movie_id = None
                    session.add(group)
                    session.commit()
                else:
                    return {"status": "current", "candidate": _candidate_payload(current)}
            else:
                return {"status": "current", "candidate": _candidate_payload(current)}

    # Otherwise, prefer pre-generated queue when available/finalized
    _res = session.exec(select(MovieCandidate.title).where(
        MovieCandidate.group_id == group.id))
    try:
        _titles = _res.scalars().all()
    except AttributeError:
        # Some SQLModel/SQLAlchemy versions return ScalarResult directly
        _titles = _res.all()
    used = set(_titles)
    shared = _shared_providers(session, group.id)
    finalized = _finalized_genres(session, group.id)
    # Preserve finalized order (most-voted first) for tiered recommendation priority
    genres_ordered = finalized if finalized else None

    # If genres are finalized but we have pre-finalization candidates (e.g., demo/on-demand), purge and rebuild
    if genres_ordered and (os.getenv("TMDB_READ_TOKEN") or os.getenv("TMDB_API_KEY")):
        existing_cands = session.exec(
            select(MovieCandidate).where(MovieCandidate.group_id ==
                                         group.id).order_by(MovieCandidate.id.asc())
        ).all()
        if existing_cands:
            try:
                first_meta = json.loads(
                    existing_cands[0].metadata_json or "{}")
            except Exception:
                first_meta = {}
            reason = first_meta.get("reason") if isinstance(
                first_meta, dict) else None
            is_queue = isinstance(
                reason, str) and reason.startswith("tmdb:queue")
            if not is_queue:
                # Clear movie votes and candidates; reset current pointer so we can build the proper queue
                for mv in session.exec(select(MovieVote).where(MovieVote.group_id == group.id)).all():
                    session.delete(mv)
                for mc in existing_cands:
                    session.delete(mc)
                group.current_movie_id = None
                session.add(group)
                session.commit()

    # If no candidates exist yet and genres are finalized, prebuild a queue of up to 100 movies
    existing_any = session.exec(select(MovieCandidate).where(
        MovieCandidate.group_id == group.id)).first()
    if genres_ordered and not existing_any:
        queue = get_candidate_queue(
            genres=genres_ordered, shared_providers=shared, target_size=100)
        if queue:
            for it in queue:
                session.add(
                    MovieCandidate(
                        group_id=group.id,
                        title=it.get("title"),
                        source=it.get("source", "tmdb"),
                        metadata_json=json.dumps({
                            "year": it.get("year"),
                            "description": it.get("description"),
                            "poster_url": it.get("poster_url"),
                            "providers": it.get("providers", []),
                            "rotten_tomatoes": it.get("rotten_tomatoes"),
                            "reason": it.get("reason"),
                        }),
                        disqualified=False,
                    )
                )
            session.commit()
            # Set current to the first non-disqualified entry in the queue
            first = session.exec(
                select(MovieCandidate)
                .where(MovieCandidate.group_id == group.id, MovieCandidate.disqualified == False)  # noqa: E712
                .order_by(MovieCandidate.id.asc())
            ).first()
            if first:
                group.current_movie_id = first.id
                session.add(group)
                session.commit()
                return {"status": "current", "candidate": _candidate_payload(first)}

    # If we already have a persisted queue but no current, advance to next
    if not group.current_movie_id:
        next_cand = session.exec(
            select(MovieCandidate)
            .where(MovieCandidate.group_id == group.id, MovieCandidate.disqualified == False)  # noqa: E712
            .order_by(MovieCandidate.id.asc())
        ).first()
        if next_cand:
            group.current_movie_id = next_cand.id
            session.add(group)
            session.commit()
            return {"status": "current", "candidate": _candidate_payload(next_cand)}

    # On-demand single pick (pre-movie_selection or when no prebuilt queue)
    item = get_next_candidate(
        used_titles=used, shared_providers=shared, genres=genres_ordered)
    if not item:
        # Try without genre filter
        item = get_next_candidate(
            used_titles=used, shared_providers=shared, genres=None)
    if not item:
        # Absolute last attempt within TMDb: ignore used/providers/genres
        item = get_next_candidate(
            used_titles=set(), shared_providers=None, genres=None)
    if not item:
        # TMDb-only mode: never fall back to demo/static items
        msg = "TMDb not configured (set TMDB_READ_TOKEN or TMDB_API_KEY)" if not tmdb_configured else "No TMDb candidates available; please retry or reset genres"
        raise HTTPException(status_code=503, detail=msg)

    movie = MovieCandidate(
        group_id=group.id,
        title=item["title"],
        source=item.get("source", "tmdb"),
        metadata_json=json.dumps({
            "year": item.get("year"),
            "description": item.get("description"),
            "poster_url": item.get("poster_url"),
            "providers": item.get("providers", []),
            "rotten_tomatoes": item.get("rotten_tomatoes"),
            "reason": item.get("reason"),
        }),
        disqualified=False,
    )
    session.add(movie)
    session.commit()
    session.refresh(movie)
    group.current_movie_id = movie.id
    session.add(group)
    session.commit()
    return {"status": "current", "candidate": _candidate_payload(movie)}


class VoteIn(BaseModel):
    accept: bool


@app.post("/groups/{code}/movies/vote")
def vote_current_movie(code: str, payload: VoteIn, token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    ensure_tables(session)
    group = session.exec(select(Group).where(Group.code == code)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    participant = _require_member(session, group, token)
    if not group.current_movie_id:
        raise HTTPException(status_code=409, detail="No active candidate")
    current = session.get(MovieCandidate, group.current_movie_id)
    if not current or current.disqualified:
        raise HTTPException(status_code=409, detail="No active candidate")

    # Upsert vote
    existing = session.exec(
        select(MovieVote).where(
            MovieVote.group_id == group.id,
            MovieVote.participant_id == participant.id,
        )
    ).first()
    if existing:
        existing.movie_id = current.id
        existing.value = 1 if payload.accept else 0
        session.add(existing)
    else:
        session.add(
            MovieVote(
                group_id=group.id,
                participant_id=participant.id,
                movie_id=current.id,
                value=1 if payload.accept else 0,
            )
        )
    session.commit()

    # Tally (without exposing counts to clients)
    votes = session.exec(
        select(MovieVote).where(MovieVote.group_id ==
                                group.id, MovieVote.movie_id == current.id)
    ).all()
    total_participants = len(session.exec(
        select(Participant).where(Participant.group_id == group.id)).all())
    yes = sum(1 for v in votes if v.value == 1)
    no = sum(1 for v in votes if v.value == 0)

    # Strict majority accept -> finalize
    if yes > total_participants / 2:
        group.winner_movie_id = current.id
        group.phase = "finalized"
        session.add(group)
        session.commit()
        return {"status": "finalized", "winner": _candidate_payload(current)}

    # Strict majority reject -> move to next
    if no > total_participants / 2:
        current.disqualified = True
        session.add(current)
        # Clear votes for this movie
        for v in votes:
            session.delete(v)
        group.current_movie_id = None
        session.add(group)
        session.commit()
        # Auto-move to next candidate
        return get_current_movie(code=code, token=token, session=session)

    # Otherwise still pending
    return {"status": "pending"}


@app.post("/groups/{code}/veto/use")
def use_veto(code: str, token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    ensure_tables(session)
    group = session.exec(select(Group).where(Group.code == code)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    participant = _require_member(session, group, token)
    if not group.veto_enabled:
        raise HTTPException(status_code=409, detail="Veto mode is not enabled")
    if participant.veto_used:
        raise HTTPException(status_code=409, detail="Veto already used")

    if not group.current_movie_id:
        raise HTTPException(status_code=409, detail="No active candidate")
    current = session.get(MovieCandidate, group.current_movie_id)
    if not current or current.disqualified:
        raise HTTPException(status_code=409, detail="No active candidate")

    # Use veto without revealing who
    current.disqualified = True
    participant.veto_used = True
    participant.has_veto = True  # ensure flag
    session.add(current)
    session.add(participant)
    # Clear votes for this movie
    votes = session.exec(
        select(MovieVote).where(MovieVote.group_id ==
                                group.id, MovieVote.movie_id == current.id)
    ).all()
    for v in votes:
        session.delete(v)
    group.current_movie_id = None
    session.add(group)
    session.commit()

    # Move to next candidate
    return get_current_movie(code=code, token=token, session=session)


@app.get("/", response_class=HTMLResponse)
def homepage():
    return (
        """
        <html>
          <head>
            <title>Login • MovieRecommender</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <style>
              :root { --primary: #2563eb; --primary-hover:#1d4ed8; }
              body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 2rem; background: #f8fafc; }
              .card { max-width: 420px; padding: 1.25rem 1.5rem; border: 1px solid #e5e7eb; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); background: white; margin: 0 auto; }
              h1 { margin: 0 0 .5rem 0; font-size: 1.5rem; }
              label { display:block; font-size: .95rem; margin-top: .75rem; color: #374151; }
              input { width: 100%; padding: .6rem .7rem; margin-top: .35rem; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem; }
              button { width: 100%; margin-top: 1rem; background: var(--primary); color: white; padding: .7rem 1rem; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }
              button:hover { background: var(--primary-hover); }
              .muted { color: #6b7280; font-size: .95rem; }
              .row { display:flex; justify-content: space-between; align-items:center; margin-top: .75rem; }
              .link { color: var(--primary); text-decoration: none; }
              .msg { margin-top: .75rem; font-size:.95rem; }
              pre { white-space: pre-wrap; word-break: break-word; background:#f3f4f6; padding:.5rem; border-radius:8px; }
            </style>
          </head>
          <body>
            <div class="card">
              <h1>Welcome back</h1>
              <p class="muted">Sign in to continue to MovieRecommender.</p>
              <form id="loginForm">
                <label for="email">Email</label>
                <input id="email" name="username" type="email" required placeholder="you@example.com" />
                <label for="password">Password</label>
                <input id="password" name="password" type="password" minlength="8" maxlength="32" required placeholder="••••••••" />
                <button type="submit">Sign in</button>
                <div class="row">
                  <span class="muted">No account?</span>
                  <a class="link" href="/register">Create one</a>
                </div>
              </form>
              <div id="status" class="msg"></div>
              <div id="meBox" style="display:none;">
                <p class="muted">You are signed in as:</p>
                <pre id="me"></pre>
              </div>
            </div>
            <script>
              const form = document.getElementById('loginForm');
              const statusEl = document.getElementById('status');
              const meBox = document.getElementById('meBox');
              const meEl = document.getElementById('me');

              function showStatus(msg, ok=false){
                statusEl.textContent = msg;
                statusEl.style.color = ok ? '#065f46' : '#7f1d1d';
              }

              async function fetchMe(token){
                const r = await fetch('/me', { headers: { 'Authorization': 'Bearer ' + token } });
                if(r.ok){
                  const data = await r.json();
                  meEl.textContent = JSON.stringify(data, null, 2);
                  meBox.style.display = 'block';
                }
              }

              // If token in localStorage, show current user
              const saved = localStorage.getItem('access_token');
              if(saved){ fetchMe(saved); }

              form.addEventListener('submit', async (e)=>{
                e.preventDefault();
                showStatus('Signing in...');
                const formData = new FormData(form);
                const body = new URLSearchParams(formData);
                const r = await fetch('/auth/login', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                  body
                });
                if(r.ok){
                  const data = await r.json();
                  const token = data.access_token;
                  localStorage.setItem('access_token', token);
                  showStatus('Signed in successfully.', true);
                  await fetchMe(token);
                } else {
                  const err = await r.json().catch(()=>({detail:'Login failed'}));
                  showStatus(err.detail || 'Login failed');
                }
              });
            </script>
          </body>
        </html>
        """
    )


@app.get("/register", response_class=HTMLResponse)
def register_page():
    return (
        """
        <html>
          <head>
            <title>Register • MovieRecommender</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <style>
              :root { --primary: #2563eb; --primary-hover:#1d4ed8; }
              body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 2rem; background: #f8fafc; }
              .card { max-width: 420px; padding: 1.25rem 1.5rem; border: 1px solid #e5e7eb; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); background: white; margin: 0 auto; }
              h1 { margin: 0 0 .5rem 0; font-size: 1.5rem; }
              label { display:block; font-size: .95rem; margin-top: .75rem; color: #374151; }
              input { width: 100%; padding: .6rem .7rem; margin-top: .35rem; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem; }
              button { width: 100%; margin-top: 1rem; background: var(--primary); color: white; padding: .7rem 1rem; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }
              button:hover { background: var(--primary-hover); }
              .muted { color: #6b7280; font-size: .95rem; }
              .row { display:flex; justify-content: space-between; align-items:center; margin-top: .75rem; }
              .link { color: var(--primary); text-decoration: none; }
              .msg { margin-top: .75rem; font-size:.95rem; }
            </style>
          </head>
          <body>
            <div class="card">
              <h1>Create your account</h1>
              <p class="muted">Sign up to start using MovieRecommender.</p>
              <form id="regForm">
                <label for="email">Email</label>
                <input id="email" name="email" type="email" required placeholder="you@example.com" />
                <label for="password">Password</label>
                <input id="password" name="password" type="password" minlength="8" maxlength="32" required placeholder="8 to 32 characters" />
                <button type="submit">Create account</button>
                <div class="row">
                  <span class="muted">Already have an account?</span>
                  <a class="link" href="/">Sign in</a>
                </div>
              </form>
              <div id="status" class="msg"></div>
            </div>
            <script>
              const form = document.getElementById('regForm');
              const statusEl = document.getElementById('status');
              function showStatus(msg, ok=false){
                statusEl.textContent = msg;
                statusEl.style.color = ok ? '#065f46' : '#7f1d1d';
              }
              form.addEventListener('submit', async (e)=>{
                e.preventDefault();
                showStatus('Creating account...');
                const email = form.email.value.trim();
                const password = form.password.value;
                const r = await fetch('/auth/register', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ email, password })
                });
                if(r.status === 201){
                  showStatus('Account created! Redirecting to sign in...', true);
                  setTimeout(()=>{ window.location.href = '/'; }, 900);
                } else {
                  const err = await r.json().catch(()=>({detail:'Registration failed'}));
                  showStatus(err.detail || 'Registration failed');
                }
              });
            </script>
          </body>
        </html>
        """
    )


# ---- Genre nomination and voting ----
ALLOWED_GENRES = [
    "Action", "Comedy", "Drama", "Thriller", "Horror", "Sci-Fi", "Romance", "Animation",
    "Family", "Adventure", "Documentary", "Fantasy", "Mystery", "Crime"
]
_GENRE_MAP = {g.lower(): g for g in ALLOWED_GENRES}


def _canonical_genre(name: str) -> Optional[str]:
    if not isinstance(name, str):
        return None
    return _GENRE_MAP.get(name.strip().lower())


def _genre_tally(session: Session, group_id: int) -> list[dict]:
    rows = session.exec(select(GenreNomination).where(
        GenreNomination.group_id == group_id)).all()
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.genre] = counts.get(r.genre, 0) + 1
    out = [{"genre": g, "count": c} for g, c in counts.items()]
    out.sort(key=lambda x: (-x["count"], x["genre"]))
    return out


@app.post("/groups/{code}/genres/nominate")
def nominate_genres(
    code: str,
    payload: GenresNominateIn,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
):
    ensure_tables(session)
    group = session.exec(select(Group).where(Group.code == code)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    participant = _require_member(session, group, token)

    # Canonicalize and de-duplicate input
    raw = payload.genres or []
    canon = []
    seen = set()
    for g in raw:
        cg = _canonical_genre(g)
        if not cg:
            raise HTTPException(status_code=400, detail=f"Invalid genre: {g}")
        if cg not in seen:
            canon.append(cg)
            seen.add(cg)
    if len(canon) == 0:
        raise HTTPException(
            status_code=400, detail="At least one valid genre required")
    if len(canon) > 2:
        raise HTTPException(
            status_code=400, detail="Maximum 2 genres per nomination request")

    # Enforce per-participant limit of 2 total nominations
    existing = session.exec(
        select(GenreNomination).where(
            GenreNomination.group_id == group.id,
            GenreNomination.participant_id == participant.id,
        )
    ).all()
    if len(existing) >= 2:
        raise HTTPException(
            status_code=409, detail="Nomination limit reached (2)")
    remaining = 2 - len(existing)
    if len(canon) > remaining:
        raise HTTPException(
            status_code=409, detail="Nomination would exceed limit (2)")

    # Create any missing nominations
    existing_genres = {e.genre for e in existing}
    created = 0
    for g in canon:
        if g in existing_genres:
            continue
        session.add(GenreNomination(group_id=group.id,
                    participant_id=participant.id, genre=g))
        created += 1
    if created:
        session.commit()
        _maybe_advance_after_nominations(session, group)

    return {"ok": True, "nominations": _genre_tally(session, group.id)}


@app.get("/groups/{code}/genres/nominations")
def list_nominations(code: str, token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    ensure_tables(session)
    group = session.exec(select(Group).where(Group.code == code)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    _require_member(session, group, token)
    return {"nominations": _genre_tally(session, group.id), "allowed": ALLOWED_GENRES}


@app.post("/groups/{code}/genres/vote")
def vote_genre(
    code: str,
    payload: GenreVoteIn,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
):
    ensure_tables(session)
    group = session.exec(select(Group).where(Group.code == code)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    participant = _require_member(session, group, token)

    cg = _canonical_genre(payload.genre)
    if not cg:
        raise HTTPException(status_code=400, detail="Invalid genre")

    # Must be a nominated genre by someone in the group
    any_nom = session.exec(
        select(GenreNomination).where(GenreNomination.group_id ==
                                      group.id, GenreNomination.genre == cg)
    ).first()
    if not any_nom:
        raise HTTPException(status_code=400, detail="Genre not nominated")

    # Enforce max 3 votes per participant across genres
    existing_votes = session.exec(
        select(GenreVote).where(GenreVote.group_id == group.id,
                                GenreVote.participant_id == participant.id)
    ).all()
    if any(v.genre == cg for v in existing_votes):
        # idempotent
        return {"ok": True, "voted": cg}
    if len(existing_votes) >= 3:
        raise HTTPException(status_code=409, detail="Vote limit reached (3)")

    session.add(GenreVote(group_id=group.id,
                participant_id=participant.id, genre=cg, value=1))
    session.commit()
    _maybe_finalize_after_votes(session, group)
    return {"ok": True, "voted": cg}


@app.get("/groups/{code}/genres/standings")
def genre_standings(code: str, token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    """Return vote tallies for nominated genres and the current plurality leader.
    Does not advance any phase; purely informational for the UI.
    """
    ensure_tables(session)
    group = session.exec(select(Group).where(Group.code == code)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    _require_member(session, group, token)

    # Build tally for votes
    votes = session.exec(select(GenreVote).where(
        GenreVote.group_id == group.id)).all()
    vcounts: dict[str, int] = {}
    for v in votes:
        vcounts[v.genre] = vcounts.get(v.genre, 0) + (v.value or 0)
    standings = [{"genre": g, "votes": c} for g, c in vcounts.items()]
    standings.sort(key=lambda x: (-x["votes"], x["genre"]))
    leader = standings[0]["genre"] if standings else None

    return {
        "standings": standings,
        "leader": leader,
        "nominations": _genre_tally(session, group.id),
        "allowed": ALLOWED_GENRES,
    }


@app.post("/groups/{code}/genres/reset")
def reset_genres(code: str, token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    """Host-only: restart the movie recommendation process back to genre nomination.

    Clears all genre nominations, votes, and finalized genres; clears movie votes and
    candidates; resets current and winner; and sets the phase to "genre_nomination".
    """
    ensure_tables(session)
    group = session.exec(select(Group).where(Group.code == code)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    caller = _require_member(session, group, token)
    if not caller.is_host:
        raise HTTPException(
            status_code=403, detail="Only host can reset genres")

    # Delete genre votes, nominations, finalized
    for v in session.exec(select(GenreVote).where(GenreVote.group_id == group.id)).all():
        session.delete(v)
    for n in session.exec(select(GenreNomination).where(GenreNomination.group_id == group.id)).all():
        session.delete(n)
    for f in session.exec(select(GenreFinalized).where(GenreFinalized.group_id == group.id)).all():
        session.delete(f)
    # Delete movie votes and candidates; reset pointers
    for mv in session.exec(select(MovieVote).where(MovieVote.group_id == group.id)).all():
        session.delete(mv)
    for mc in session.exec(select(MovieCandidate).where(MovieCandidate.group_id == group.id)).all():
        session.delete(mc)
    group.current_movie_id = None
    group.winner_movie_id = None
    group.phase = "genre_nomination"
    session.add(group)
    session.commit()
    return {"ok": True, "phase": group.phase}


# ---- Progress and phase helpers ----


def _participants_in_group(session: Session, group_id: int) -> list[Participant]:
    return session.exec(select(Participant).where(Participant.group_id == group_id)).all()


def _count_distinct_nominees(session: Session, group_id: int) -> int:
    rows = session.exec(select(GenreNomination.participant_id).where(
        GenreNomination.group_id == group_id)).all()
    return len(set(rows))


def _count_distinct_voters(session: Session, group_id: int) -> int:
    rows = session.exec(select(GenreVote.participant_id).where(
        GenreVote.group_id == group_id)).all()
    return len(set(rows))


def _finalized_genres(session: Session, group_id: int) -> list[str]:
    rows = session.exec(select(GenreFinalized).where(
        GenreFinalized.group_id == group_id)).all()
    return [r.genre for r in rows]


def _maybe_advance_after_nominations(session: Session, group: Group):
    parts = _participants_in_group(session, group.id)
    total = len(parts)
    if total == 0:
        return
    # If only one participant is in the group, auto-finalize their nominations (up to two) and skip voting
    if total == 1:
        # collect that participant's nominations
        noms = session.exec(select(GenreNomination).where(
            GenreNomination.group_id == group.id)).all()
        if noms:
            # clear any existing finalized
            for old in session.exec(select(GenreFinalized).where(GenreFinalized.group_id == group.id)).all():
                session.delete(old)
            # take up to two unique genres in a stable order by insertion id
            seen: set[str] = set()
            taken = 0
            for n in sorted(noms, key=lambda x: x.id or 0):
                if n.genre in seen:
                    continue
                session.add(GenreFinalized(group_id=group.id, genre=n.genre))
                seen.add(n.genre)
                taken += 1
                if taken >= 2:
                    break
            group.phase = "movie_selection"
            session.add(group)
            session.commit()
            return
    # Multi-participant path: once everyone has nominated at least one, advance to voting
    nominated = _count_distinct_nominees(session, group.id)
    if nominated >= total and (session.exec(select(GenreNomination).where(GenreNomination.group_id == group.id)).first() is not None):
        group.phase = "genre_voting"
        session.add(group)
        session.commit()


def _maybe_finalize_after_votes(session: Session, group: Group):
    parts = _participants_in_group(session, group.id)
    total = len(parts)
    if total == 0:
        return
    voted = _count_distinct_voters(session, group.id)
    # Build vote tally
    votes = session.exec(select(GenreVote).where(
        GenreVote.group_id == group.id)).all()
    if voted >= total and votes:
        tally = Counter()
        for v in votes:
            tally[v.genre] += (v.value or 0)
        top2 = [g for g, _c in tally.most_common(2)]
        if len(top2) >= 2:
            # reset and store finalized genres
            for old in session.exec(select(GenreFinalized).where(GenreFinalized.group_id == group.id)).all():
                session.delete(old)
            for gname in top2:
                session.add(GenreFinalized(group_id=group.id, genre=gname))
            group.phase = "movie_selection"
            session.add(group)
            session.commit()


@app.get("/groups/{code}/progress")
def group_progress(code: str, token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    ensure_tables(session)
    group = session.exec(select(Group).where(Group.code == code)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    _require_member(session, group, token)
    parts = _participants_in_group(session, group.id)
    total = len(parts)
    nominated = _count_distinct_nominees(session, group.id)
    voted = _count_distinct_voters(session, group.id)
    finalized = _finalized_genres(session, group.id)

    # Include winner movie if finalized
    winner_movie = None
    if group.phase == "finalized" and group.winner_movie_id:
        winner = session.get(MovieCandidate, group.winner_movie_id)
        if winner:
            winner_movie = _candidate_payload(winner)

    return {
        "phase": group.phase,
        "total_participants": total,
        "nominated_count": nominated,
        "voted_count": voted,
        "all_nominated": nominated >= total and total > 0,
        "all_voted": voted >= total and total > 0,
        "finalized_genres": finalized,
        "winner_movie": winner_movie,
    }
