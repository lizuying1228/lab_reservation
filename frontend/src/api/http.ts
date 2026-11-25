import axios from 'axios'
import router from '../router'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = false
let waiting: Array<(token: string | null) => void> = []

http.interceptors.response.use(
  response => response,
  async error => {
    const original = error.config
    if (error.response?.status === 401 && original && !original._retry &&
        !String(original.url).includes('/users/login/') &&
        !String(original.url).includes('/users/token/refresh/')) {
      const refresh = localStorage.getItem('refresh')
      if (!refresh) {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        if (router.currentRoute.value.path !== '/login') await router.push('/login')
        return Promise.reject(error)
      }
      if (refreshing) {
        return new Promise((resolve, reject) => {
          waiting.push((token) => {
            if (!token) return reject(error)
            original.headers.Authorization = `Bearer ${token}`
            resolve(http(original))
          })
        })
      }
      original._retry = true
      refreshing = true
      try {
        const { data } = await axios.post(
          `${http.defaults.baseURL}/users/token/refresh/`, { refresh }
        )
        localStorage.setItem('access', data.access)
        waiting.forEach(cb => cb(data.access))
        waiting = []
        original.headers.Authorization = `Bearer ${data.access}`
        return http(original)
      } catch (refreshError) {
        waiting.forEach(cb => cb(null))
        waiting = []
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        if (router.currentRoute.value.path !== '/login') await router.push('/login')
        return Promise.reject(refreshError)
      } finally {
        refreshing = false
      }
    }
    return Promise.reject(error)
  }
)

export default http

export function errorMessage(error: any): string {
  const data = error?.response?.data
  if (!data) return error?.message || '网络连接失败，请检查后端服务'
  if (typeof data === 'string') return data
  const values: string[] = []
  const walk = (value: any) => {
    if (typeof value === 'string') values.push(value)
    else if (Array.isArray(value)) value.forEach(walk)
    else if (value && typeof value === 'object') Object.values(value).forEach(walk)
  }
  walk(data)
  return values.filter(Boolean).join('；') || `请求失败（${error.response.status}）`
}
