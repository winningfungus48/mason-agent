/**
 * FastAPI base URL and dashboard API key.
 * Prefer `VITE_API_URL` + `VITE_API_KEY` in `.env.local` (see Vite docs).
 */
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) ??
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  ''
