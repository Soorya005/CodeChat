/**
 * lib/api.ts
 * Central API client — all calls to the FastAPI backend go through here.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
const queryTimeoutMsEnv = Number(process.env.NEXT_PUBLIC_QUERY_TIMEOUT_MS)
const QUERY_TIMEOUT_MS = Number.isFinite(queryTimeoutMsEnv) && queryTimeoutMsEnv > 0
  ? queryTimeoutMsEnv
  : 180000

// ─── Helpers ────────────────────────────────────────────────────────────────

function authHeaders(token: string) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? JSON.stringify(body)
    } catch {
      // ignore json parse error
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export async function apiRegister(
  username: string,
  password: string
): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  })
  return handleResponse(res)
}

export async function apiLogin(
  username: string,
  password: string
): Promise<{ access_token: string; token_type: string }> {
  const formData = new URLSearchParams()
  formData.append("username", username)
  formData.append("password", password)

  const res = await fetch(`${BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData.toString(),
  })
  return handleResponse(res)
}

// ─── Repository ──────────────────────────────────────────────────────────────

export async function apiAddRepository(
  token: string,
  repo_url: string
): Promise<{ repository_id: number; repo_url: string; status: string }> {
  const res = await fetch(
    `${BASE_URL}/repository/add?repo_url=${encodeURIComponent(repo_url)}`,
    { method: "POST", headers: authHeaders(token) }
  )
  return handleResponse(res)
}

export async function apiIndexRepository(
  token: string,
  repo_id: number
): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/repository/index/${repo_id}`, {
    method: "POST",
    headers: authHeaders(token),
  })
  return handleResponse(res)
}

export async function apiGetRepositoryStatus(
  token: string,
  repo_id: number
): Promise<{ repo_id: number; status: string; faiss_index_path: string | null }> {
  const res = await fetch(`${BASE_URL}/repository/status/${repo_id}`, {
    headers: authHeaders(token),
  })
  return handleResponse(res)
}

export async function apiListRepositories(
  token: string
): Promise<{ id: number; repo_url: string; status: string }[]> {
  const res = await fetch(`${BASE_URL}/repository/list`, {
    headers: authHeaders(token),
  })
  return handleResponse(res)
}

export interface RepositoryTreeNode {
  name: string
  path: string
  type: "directory" | "file"
  children?: RepositoryTreeNode[]
}

export interface RepositoryFileContent {
  repo_id: number
  file_path: string
  content: string
  truncated: boolean
}

export async function apiGetRepositoryTree(
  token: string,
  repo_id: number
): Promise<{ repo_id: number; tree: RepositoryTreeNode[] }> {
  const res = await fetch(`${BASE_URL}/repository/tree/${repo_id}`, {
    headers: authHeaders(token),
  })
  return handleResponse(res)
}

export async function apiGetRepositoryFileContent(
  token: string,
  repo_id: number,
  file_path: string
): Promise<RepositoryFileContent> {
  const res = await fetch(
    `${BASE_URL}/repository/file-content/${repo_id}?file_path=${encodeURIComponent(file_path)}`,
    {
      headers: authHeaders(token),
    }
  )
  return handleResponse(res)
}

// ─── Chat / Query ─────────────────────────────────────────────────────────────

export interface QuerySource {
  file: string
  symbol: string
  line: number
}

export interface QueryResponse {
  answer: string
  sources: QuerySource[]
}

export async function apiQueryRepository(
  token: string,
  repo_id: number,
  query: string
): Promise<QueryResponse> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), QUERY_TIMEOUT_MS)

  try {
    const res = await fetch(
      `${BASE_URL}/chat/query?repo_id=${repo_id}&query=${encodeURIComponent(query)}`,
      { method: "POST", headers: authHeaders(token), signal: controller.signal }
    )
    return handleResponse(res)
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(
        `Request timed out after ${Math.floor(QUERY_TIMEOUT_MS / 1000)} seconds. Please try again.`
      )
    }
    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}

export interface ChatHistoryItem {
  id: number
  repository_url: string
  query_text: string
  response_text: string
}

export async function apiGetChatHistory(
  token: string
): Promise<ChatHistoryItem[]> {
  const res = await fetch(`${BASE_URL}/chat/history`, {
    headers: authHeaders(token),
  })
  return handleResponse(res)
}

export async function apiGetRepoChatHistory(
  token: string,
  repository_url: string
): Promise<ChatHistoryItem[]> {
  const res = await fetch(
    `${BASE_URL}/chat/repository?repository_url=${encodeURIComponent(repository_url)}`,
    { headers: authHeaders(token) }
  )
  return handleResponse(res)
}
