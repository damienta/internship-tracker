import axios from 'axios'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL
const normalizedBaseUrl = configuredBaseUrl
  ? configuredBaseUrl.replace(/\/+$/, '')
  : '/api'

const api = axios.create({
  baseURL: normalizedBaseUrl,
})

export default api
