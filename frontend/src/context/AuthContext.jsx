import { createContext, useContext, useEffect, useState } from 'react'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user')
    // Sessions saved without a token can't make authenticated requests, so start logged out
    return stored && localStorage.getItem('token') ? JSON.parse(stored) : null
  })

  const login = (userData, token) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(userData))
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  // Fired by the API client when the backend rejects the token
  useEffect(() => {
    const handleExpired = () => {
      if (!localStorage.getItem('user')) return
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      setUser(null)
      toast.error('Your session has expired. Please log in again.', { id: 'session-expired' })
    }
    window.addEventListener('auth:expired', handleExpired)
    return () => window.removeEventListener('auth:expired', handleExpired)
  }, [])

  const updateUser = (partialUserData) => { // Ensures all updates to user data are synced
    setUser((prev) => {
      const next = { ...(prev || {}), ...(partialUserData || {}) }
      localStorage.setItem('user', JSON.stringify(next))
      return next
    })
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
