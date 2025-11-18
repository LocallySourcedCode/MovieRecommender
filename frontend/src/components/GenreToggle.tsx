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
      <div style={{ marginBottom: 6 }}>Pick up to {max} genres:</div>
      <div role="group" aria-label="Genres" style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
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
              style={{
                padding: '6px 10px',
                borderRadius: 6,
                border: '1px solid #ccc',
                background: active ? '#10b981' : 'white',
                color: active ? 'white' : 'black',
                cursor: disabled ? 'not-allowed' : 'pointer',
                opacity: disabled ? 0.6 : 1,
              }}
            >
              {g}
            </button>
          )
        })}
      </div>
    </div>
  )
}
