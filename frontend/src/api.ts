export type SourceItem = {
  filename: string
  page: number | null
  chunk_index: number
  snippet: string
  similarity: number
}

export type AskResponse = {
  answer: string
  sources: SourceItem[]
  grounded: boolean
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch(`${API_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: 5 }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail ?? 'Request failed')
  }

  return response.json() as Promise<AskResponse>
}

export async function ingestFolder(): Promise<{ ingested: number; total_chunks: number; documents: string[] }> {
  const response = await fetch(`${API_URL}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: 'documents' }),
  })

  if (!response.ok) {
    throw new Error('Ingestion failed')
  }

  return response.json()
}
