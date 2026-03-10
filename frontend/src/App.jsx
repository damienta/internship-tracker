import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import Opportunities from './pages/Opportunities'
import Tracker from './pages/Tracker'
import About from './pages/About'
import Login from './pages/Login'
import Register from './pages/Register'

// Wraps a route so unauthenticated users are sent to /login
function PrivateRoute({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" replace />
}

// Redirects already-logged-in users away from /login and /register
function GuestRoute({ children }) {
  const { user } = useAuth()
  return user ? <Navigate to="/" replace /> : children
}

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <p>404 - Page not found</p>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Guest-only routes (no layout/navbar) */}
        <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
        <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />

        {/* Protected routes (require login) */}
        <Route element={<Layout />}>
          <Route path="/" element={<PrivateRoute><Home /></PrivateRoute>} />
          <Route path="/opportunities" element={<PrivateRoute><Opportunities /></PrivateRoute>} />
          <Route path="/tracker" element={<PrivateRoute><Tracker /></PrivateRoute>} />
          <Route path="/about" element={<PrivateRoute><About /></PrivateRoute>} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App
