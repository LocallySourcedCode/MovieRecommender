#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
GENRE1="${1:-Comedy}"
GENRE2="${2:-Thriller}"
VOTES="${VOTES:-5}"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Error: missing dependency '$1'. Please install it (e.g., sudo apt-get install $1)." >&2; exit 1; }
}

need curl
need jq

info() { echo "[SMOKE] $*"; }

# Check TMDb configuration
CFG=$(curl -sS "${API_BASE}/config" || true)
TMDB=$(echo "$CFG" | jq -r '.tmdb_configured // false' 2>/dev/null || echo "false")
REGION=$(echo "$CFG" | jq -r '.tmdb_region // ""' 2>/dev/null || echo "")
info "API_BASE=${API_BASE} TMDB_CONFIGURED=${TMDB} REGION=${REGION}"
if [ "$TMDB" != "true" ]; then
  echo "Error: TMDb is not configured on the server. Set TMDB_READ_TOKEN or TMDB_API_KEY in the API environment and retry." >&2
  exit 2
fi

# Create a group as guest
RESP=$(curl -sS -X POST "${API_BASE}/groups" \
  -H 'Content-Type: application/json' \
  -d '{"display_name":"SmokeRunner","streaming_services":["netflix","hulu","amazon","hbo"]}')
TOKEN=$(echo "$RESP" | jq -r '.access_token')
CODE=$(echo "$RESP" | jq -r '.group.code')
if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "Error: could not create group or retrieve token. Response: $RESP" >&2
  exit 3
fi
info "Created group CODE=${CODE}"

AUTH=( -H "Authorization: Bearer ${TOKEN}" )

# Nominate two genres
info "Nominating genres: ${GENRE1}, ${GENRE2}"
NOM=$(curl -sS -X POST "${API_BASE}/groups/${CODE}/genres/nominate" \
  "${AUTH[@]}" -H 'Content-Type: application/json' \
  -d "{\"genres\":[\"${GENRE1}\",\"${GENRE2}\"]}")

# Wait for phase to move to movie_selection
info "Waiting for phase=movie_selection..."
for i in {1..30}; do
  PROG=$(curl -sS "${API_BASE}/groups/${CODE}/progress" "${AUTH[@]}")
  PHASE=$(echo "$PROG" | jq -r '.phase')
  FINALIZED=$(echo "$PROG" | jq -c '.finalized_genres')
  info "Phase=$PHASE Finalized=$FINALIZED"
  if [ "$PHASE" = "movie_selection" ] || [ "$PHASE" = "finalized" ]; then
    break
  fi
  sleep 1
  if [ $i -eq 30 ]; then
    echo "Error: phase did not advance to movie_selection within timeout." >&2
    exit 4
  fi
done

# Fetch current movie
CUR=$(curl -sS "${API_BASE}/groups/${CODE}/movies/current" "${AUTH[@]}")
STATUS=$(echo "$CUR" | jq -r '.status // empty')
TITLE=$(echo "$CUR" | jq -r '.candidate.title // .winner.title // empty')
REASON=$(echo "$CUR" | jq -r '.candidate.source + ":" + (.candidate.reason // "") // .winner.source + ":" + (.winner.reason // "") // empty')
if [ -z "$TITLE" ]; then
  echo "Error: no current movie returned. Response: $CUR" >&2
  # Disband before exit
  curl -sS -X POST "${API_BASE}/groups/leave" "${AUTH[@]}" >/dev/null || true
  exit 5
fi
info "Current movie: ${TITLE} (${REASON})"

# Cast a series of 'No' votes to walk the queue
for ((i=1;i<=VOTES;i++)); do
  VRESP=$(curl -sS -X POST "${API_BASE}/groups/${CODE}/movies/vote" "${AUTH[@]}" -H 'Content-Type: application/json' -d '{"accept":false}')
  ST=$(echo "$VRESP" | jq -r '.status // empty')
  T=$(echo "$VRESP" | jq -r '.candidate.title // .winner.title // empty')
  R=$(echo "$VRESP" | jq -r '.candidate.source + ":" + (.candidate.reason // "") // .winner.source + ":" + (.winner.reason // "") // empty')
  if [ -z "$T" ]; then
    info "Vote response: $VRESP"
    break
  fi
  info "After vote $i -> ${ST}: ${T} (${R})"
  if [ "$ST" = "finalized" ]; then
    break
  fi
  # also fetch current explicitly
  CUR=$(curl -sS "${API_BASE}/groups/${CODE}/movies/current" "${AUTH[@]}")
  T=$(echo "$CUR" | jq -r '.candidate.title // .winner.title // empty')
  R=$(echo "$CUR" | jq -r '.candidate.source + ":" + (.candidate.reason // "") // .winner.source + ":" + (.winner.reason // "") // empty')
  if [ -n "$T" ]; then info "Current -> ${T} (${R})"; fi
  sleep 0.2
done

# Disband group (host)
info "Disbanding group ${CODE}"
curl -sS -X POST "${API_BASE}/groups/leave" "${AUTH[@]}" >/dev/null || true
info "Done."