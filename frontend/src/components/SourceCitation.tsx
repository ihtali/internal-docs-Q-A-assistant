import type { SourceItem } from '../api'

export function SourceCitation({ source }: { source: SourceItem }) {
  return (
    <details className="mt-3 rounded-xl border border-slate-700 bg-slate-900/80 p-2 text-left text-xs text-slate-200">
      <summary className="cursor-pointer list-none font-medium text-sky-300">
        {source.filename} · p.{source.page ?? 'N/A'}
      </summary>
      <p className="mt-2 whitespace-pre-wrap text-slate-300">{source.snippet}</p>
    </details>
  )
}
