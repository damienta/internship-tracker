import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    // Placeholder logo
    <nav className="bg-white border-b border-gray-200 sticky top-0">
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">

        <Link to="/" className="flex items-center gap-2 font-semibold">
          <span className="bg-blue-600 text-white text-xs font-bold w-7 h-7 rounded flex items-center justify-center">IT</span>
          InternTracker
        </Link>

        <div className="flex gap-6">
          <NavLink to="/opportunities" className={({ isActive }) => isActive ? 'text-blue-600 text-sm' : 'text-gray-500 text-sm'}>Opportunities</NavLink>
          <NavLink to="/tracker" className={({ isActive }) => isActive ? 'text-blue-600 text-sm' : 'text-gray-500 text-sm'}>Tracker</NavLink>
          <NavLink to="/about" className={({ isActive }) => isActive ? 'text-blue-600 text-sm' : 'text-gray-500 text-sm'}>About</NavLink>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-gray-500 text-sm">{user?.username}</span>
          <button onClick={handleLogout} className="text-sm text-red-500 hover:text-red-700">
            Log out
          </button>
        </div>

      </div>
    </nav>
  )
}
