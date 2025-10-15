from typing import Optional
import random
import string

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from jose import jwt, JWTError

from app.db import get_session, init_db, ensure_tables
from app.models import User, Group, Participant, MovieCandidate, MovieVote
from app.schemas import UserCreate, UserRead, Token
from app.schemas_group import (
    GroupCreateGuest,
    GroupCreateResponse,
    GroupJoinGuest,
    GroupJoinResponse,
    GroupOut,
    ParticipantOut,
)
from app.security import (
    hash_password,
    verify_password,
    create_token,
    JWT_SECRET,
    JWT_ALG,
    parse_subject,
    create_participant_token,
)
from app.services.recommendations import get_next_candidate
import json

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on app startup using modern lifespan API (on_event is deprecated)
    init_db()
    yield

app = FastAPI(title="MovieRecommender API", lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


@app.post("/auth/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, session: Session = Depends(get_session)):
    # ensure tables exist for the current connection (important for in-memory test DB)
    ensure_tables(session)
    # password policy: min 8, max 32 characters
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password too short (min 8 characters)")
    if len(payload.password) > 32:
        raise HTTPException(status_code=400, detail="Password too long (max 32 characters)")
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserRead(id=user.id, email=user.email)

@app.post("/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    # ensure tables exist for the current connection (important for in-memory test DB)
    ensure_tables(session)
    user = session.exec(select(User).where(User.email == form.username)).first()
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
    participants = session.exec(select(Participant).where(Participant.group_id == group.id)).all()
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
            raise HTTPException(status_code=401, detail="Participant not found")
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
        return {"kind": "participant", "id": obj.id, "group_id": obj.group_id, "display_name": obj.display_name}


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
        if kind != "user":
            raise HTTPException(status_code=403, detail="Only signed-in users can use bearer token here")
        # Create group with host_user_id
        group = Group(code=code, host_user_id=principal.id)
        session.add(group)
        session.commit()
        session.refresh(group)
        # Create participant for host
        display = principal.email.split("@")[0]
        host = Participant(group_id=group.id, user_id=principal.id, display_name=display, is_host=True)
        session.add(host)
        session.commit()
        group_out = _serialize_group(session, group)
        return GroupCreateResponse(group=group_out)
    else:
        # Guest path requires display_name
        if guest_payload is None or not guest_payload.display_name:
            raise HTTPException(status_code=422, detail="display_name is required for guests")
        group = Group(code=code, host_user_id=None)
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
            # idempotent join for users
            existing = session.exec(
                select(Participant).where(Participant.group_id == group.id, Participant.user_id == principal.id)
            ).first()
            if not existing:
                display = principal.email.split("@")[0]
                p = Participant(group_id=group.id, user_id=principal.id, display_name=display, is_host=False)
                session.add(p)
                session.commit()
            group_out = _serialize_group(session, group)
            return GroupJoinResponse(group=group_out)
        elif kind == "participant":
            # Participant tokens are tied to a specific group via their record
            participant = principal
            if participant.group_id != group.id:
                raise HTTPException(status_code=403, detail="Participant token belongs to a different group")
            group_out = _serialize_group(session, group)
            return GroupJoinResponse(group=group_out)
        else:
            raise HTTPException(status_code=401, detail="Invalid token subject")
    else:
        # Guest join requires display_name
        if guest_payload is None or not guest_payload.display_name:
            raise HTTPException(status_code=422, detail="display_name is required for guests")
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
    participants = session.exec(select(Participant).where(Participant.group_id == group_id)).all()
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
            raise HTTPException(status_code=403, detail="Participant token belongs to a different group")
        return obj
    elif kind == "user":
        p = session.exec(
            select(Participant).where(Participant.group_id == group.id, Participant.user_id == obj.id)
        ).first()
        if not p:
            raise HTTPException(status_code=403, detail="You are not a member of this group")
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

    # If current exists and is not disqualified, return it
    if group.current_movie_id:
        current = session.get(MovieCandidate, group.current_movie_id)
        if current and not current.disqualified:
            return {"status": "current", "candidate": _candidate_payload(current)}

    # Otherwise pick next compatible candidate from demo
    _res = session.exec(select(MovieCandidate.title).where(MovieCandidate.group_id == group.id))
    try:
        _titles = _res.scalars().all()
    except AttributeError:
        # Some SQLModel/SQLAlchemy versions return ScalarResult directly
        _titles = _res.all()
    used = set(_titles)
    shared = _shared_providers(session, group.id)
    item = get_next_candidate(used_titles=used, shared_providers=shared)
    if not item:
        raise HTTPException(status_code=404, detail="No more candidates available")
    movie = MovieCandidate(
        group_id=group.id,
        title=item["title"],
        source="demo",
        metadata_json=json.dumps({
            "year": item.get("year"),
            "description": item.get("description"),
            "poster_url": item.get("poster_url"),
            "providers": item.get("providers", []),
            "rotten_tomatoes": item.get("rotten_tomatoes"),
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


from pydantic import BaseModel


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
        select(MovieVote).where(MovieVote.group_id == group.id, MovieVote.movie_id == current.id)
    ).all()
    total_participants = len(session.exec(select(Participant).where(Participant.group_id == group.id)).all())
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
        select(MovieVote).where(MovieVote.group_id == group.id, MovieVote.movie_id == current.id)
    ).all()
    for v in votes:
        session.delete(v)
    group.current_movie_id = None
    session.add(group)
    session.commit()

    # Move to next candidate
    return get_current_movie(code=code, token=token, session=session)


from fastapi.responses import HTMLResponse

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
