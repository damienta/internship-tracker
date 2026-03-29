import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import Opportunities from './pages/Opportunities'
import Tracker from './pages/Tracker'
import About from './pages/About'
import Contact from './pages/Contact'
import Community from './pages/Community'
import CvTemplates from './pages/community/CvTemplates'
import CvExamples from './pages/community/CvExamples'
import CoverLetterTemplates from './pages/community/CoverLetterTemplates'
import HowToGuides from './pages/community/HowToGuides'
import CompanyRatings from './pages/community/CompanyRatings'
import CommunityDiscussion from './pages/community/CommunityDiscussion'
import Settings from './pages/Settings'
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
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 3800,
          style: {
            fontSize: '15px',
            padding: '14px 16px',
            borderRadius: '12px',
            maxWidth: '520px',
          },
          error: {
            style: {
              border: '1px solid #fecaca',
              background: '#fef2f2',
              color: '#991b1b',
            },
          },
          success: {
            style: {
              border: '1px solid #bbf7d0',
              background: '#f0fdf4',
              color: '#166534',
            },
          },
        }}
      />

      <Routes>
        {/* Guest-only routes */}
        <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
        <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />

        {/* Protected routes (requires login) */}
        <Route element={<Layout />}>
          <Route path="/" element={<PrivateRoute><Home /></PrivateRoute>} />
          <Route path="/opportunities" element={<PrivateRoute><Opportunities /></PrivateRoute>} />
          <Route path="/tracker" element={<PrivateRoute><Tracker /></PrivateRoute>} />
          <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
          <Route path="/about" element={<PrivateRoute><About /></PrivateRoute>} />
          <Route path="/community" element={<PrivateRoute><Community /></PrivateRoute>} />
          <Route path="/community/cv-templates" element={<PrivateRoute><CvTemplates /></PrivateRoute>} />
          <Route path="/community/cv-examples" element={<PrivateRoute><CvExamples /></PrivateRoute>} />
          <Route path="/community/cover-letter-templates" element={<PrivateRoute><CoverLetterTemplates /></PrivateRoute>} />
          <Route path="/community/how-to-guides" element={<PrivateRoute><HowToGuides /></PrivateRoute>} />
          <Route path="/community/company-ratings" element={<PrivateRoute><CompanyRatings /></PrivateRoute>} />
          <Route path="/community/discussion" element={<PrivateRoute><CommunityDiscussion /></PrivateRoute>} />
          <Route path="/contact-us" element={<PrivateRoute><Contact /></PrivateRoute>} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App
