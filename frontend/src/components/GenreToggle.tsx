import React from 'react'

const GENRES = [
  'Action','Comedy','Drama','Thriller','Horror','Sci-Fi','Romance','Animation',
  'Family','Adventure','Documentary','Fantasy','Mystery','Crime'
]

export function GenreToggle({ value, onChange, max = 2 }: { value: string[]; onChange: (next: string[]) => void; max?: number }) {
  function toggle(genre: string) {
    const set = new Set(value)
    if (set.has(genre)) {
      set.delete(genre)
      onChange(Array.from(set))
      return
    }
    if (set.size >= max) return
    set.add(genre)
    onChange(Array.from(set))
  }

  return (
    <div>
      <p style={{ marginBottom: '0.75rem', color: '#6b7280' }}>Choose up to {max} genres you'd like to watch</p>
      <div className="pill-group" role="group" aria-label="Genres">
        {GENRES.map(g => {
          const active = value.includes(g)
          const disabled = !active && value.length >= max
          return (
            <button
              key={g}
              type="button"
              aria-pressed={active}
              aria-disabled={disabled}
              onClick={() => toggle(g)}
              className={`pill ${active ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
            >
              {g}
            </button>
          )
        })}
      </div>
    </div>
  )
}
