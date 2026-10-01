import axios from 'axios'

export const getApiBaseUrl = (): string => {
  const rawUrl = import.meta.env.VITE_API_URL
  if (!rawUrl || typeof rawUrl !== 'string' || !rawUrl.trim()) {
    return '/api/v1'
  }
  const trimmed = rawUrl.trim().replace(/\/+$/, '')
  if (!trimmed.endsWith('/api/v1')) {
    return `${trimmed}/api/v1`
  }
  return trimmed
}

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url || ''
      const isAuthEndpoint = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/register')
      if (!isAuthEndpoint) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        if (
          typeof window !== 'undefined' &&
          !window.location.pathname.startsWith('/login') &&
          !window.location.pathname.startsWith('/register')
        ) {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)
