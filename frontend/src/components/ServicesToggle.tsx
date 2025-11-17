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
    <div className="pill-group" role="group" aria-label="Streaming services">
      {OPTIONS.map(opt => {
        const active = value.includes(opt.key)
        return (
          <button
            key={opt.key}
            type="button"
            aria-pressed={active}
            onClick={() => toggle(opt.key)}
            className={`pill ${active ? 'active' : ''}`}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
