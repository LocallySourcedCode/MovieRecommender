from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from jose import jwt, JWTError

from app.db import get_session, init_db, ensure_tables
from app.models import User
from app.schemas import UserCreate, UserRead, Token
from app.security import hash_password, verify_password, create_token, JWT_SECRET, JWT_ALG

app = FastAPI(title="MovieRecommender API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@app.on_event("startup")
def on_startup():
    init_db()

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
