import http from './http'

export type PageResult<T> = { count?: number; next?: string | null; previous?: string | null; results?: T[] } | T[]

export async function listResource<T>(path: string, params: Record<string, any> = {}): Promise<T[]> {
  const { data } = await http.get(path, { params })
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
}
export const createResource = (path: string, payload: any) => http.post(path, payload)
export const updateResource = (path: string, id: number | string, payload: any) => http.patch(`${path}${id}/`, payload)
export const deleteResource = (path: string, id: number | string) => http.delete(`${path}${id}/`)
