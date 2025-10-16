import React from 'react'

const OPTIONS = [
  { key: 'netflix', label: 'Netflix' },
  { key: 'hulu', label: 'Hulu' },
  { key: 'amazon', label: 'Amazon' },
  { key: 'hbo', label: 'HBO' },
]

export function ServicesToggle({ value, onChange }: { value: string[]; onChange: (next: string[]) => void }) {
  function toggle(key: string) {
    const set = new Set(value)
    if (set.has(key)) set.delete(key)
    else set.add(key)
    onChange(Array.from(set))
  }

  return (
    <div>
      <div style={{ marginBottom: 6 }}>Streaming services (optional):</div>
      <div role="group" aria-label="Streaming services" style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {OPTIONS.map(opt => {
          const active = value.includes(opt.key)
          return (
            <button
              key={opt.key}
              type="button"
              aria-pressed={active}
              onClick={() => toggle(opt.key)}
              style={{
                padding: '6px 10px',
                borderRadius: 6,
                border: '1px solid #ccc',
                background: active ? '#2563eb' : 'white',
                color: active ? 'white' : 'black',
                cursor: 'pointer',
              }}
            >
              {opt.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
