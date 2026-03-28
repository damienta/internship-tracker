import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import defaultPfp from '../assets/default_pfp.jpg'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const initials = (user?.username || 'U').slice(0, 2).toUpperCase()
  const [avatarLoadFailed, setAvatarLoadFailed] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">

        <Link to="/" className="flex items-center gap-2 font-semibold">
          <span className="w-7 h-7 rounded bg-slate-800 text-white text-xs font-bold flex items-center justify-center">td</span>
          tracker.dev
        </Link>

        <div className="flex gap-6">
          <NavLink to="/" className={({ isActive }) => isActive ? 'text-blue-600 text-sm font-semibold hover:text-blue-700' : 'text-gray-600 text-sm hover:text-gray-900'}>Home</NavLink>
          <NavLink to="/opportunities" className={({ isActive }) => isActive ? 'text-blue-600 text-sm font-semibold hover:text-blue-700' : 'text-gray-600 text-sm hover:text-gray-900'}>Opportunities</NavLink>
          <NavLink to="/tracker" className={({ isActive }) => isActive ? 'text-blue-600 text-sm font-semibold hover:text-blue-700' : 'text-gray-600 text-sm hover:text-gray-900'}>Tracker</NavLink>
          <NavLink to="/community" className={({ isActive }) => isActive ? 'text-blue-600 text-sm font-semibold hover:text-blue-700' : 'text-gray-600 text-sm hover:text-gray-900'}>Community</NavLink>
          <NavLink to="/about" className={({ isActive }) => isActive ? 'text-blue-600 text-sm font-semibold hover:text-blue-700' : 'text-gray-600 text-sm hover:text-gray-900'}>About</NavLink>
          <NavLink to="/contact-us" className={({ isActive }) => isActive ? 'text-blue-600 text-sm font-semibold hover:text-blue-700' : 'text-gray-600 text-sm hover:text-gray-900'}>Contact Us</NavLink>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/settings"
            className="flex items-center gap-2 rounded-full border border-gray-200 px-2.5 py-1.5 hover:bg-gray-50"
          >
            {!avatarLoadFailed ? (
              <img
                src={defaultPfp}
                alt="Profile"
                className="w-7 h-7 rounded-full object-cover"
                onError={() => setAvatarLoadFailed(true)}
              />
            ) : (
              <span className="w-7 h-7 rounded-full bg-slate-700 text-white text-xs font-semibold flex items-center justify-center">{initials}</span>
            )}
            <span className="text-sm text-gray-600">{user?.username}</span>
          </Link>
          <button
            onClick={handleLogout}
            className="text-sm font-medium text-red-700 border border-red-200 bg-red-50 px-3 py-1.5 rounded-lg hover:bg-red-100"
          >
            Log out
          </button>
        </div>

      </div>
    </nav>
  )
}
