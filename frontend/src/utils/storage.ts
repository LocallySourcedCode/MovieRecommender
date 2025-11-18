export function getToken(): string | null {
  try { return localStorage.getItem('access_token') } catch { return null }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem('access_token', token)
    else localStorage.removeItem('access_token')
  } catch {}
}

export function clearToken() { setToken(null) }
