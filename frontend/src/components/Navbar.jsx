import { Link, NavLink } from 'react-router-dom'

export default function Navbar() {
  return (
    // Placeholder logo
    <nav className="bg-white border-b border-gray-200 sticky top-0">
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">

        <Link to="/" className="flex items-center gap-2 font-semibold">
          <span className="bg-blue-600 text-white text-xs font-bold w-7 h-7 rounded flex items-center justify-center">IT</span>
          InternTracker
        </Link>

        <div className="flex gap-6">
          <NavLink to="/" className={({ isActive }) => isActive ? 'text-blue-600 text-sm' : 'text-gray-500 text-sm'}>Home</NavLink>
          <NavLink to="/opportunities" className={({ isActive }) => isActive ? 'text-blue-600 text-sm' : 'text-gray-500 text-sm'}>Opportunities</NavLink>
          <NavLink to="/tracker" className={({ isActive }) => isActive ? 'text-blue-600 text-sm' : 'text-gray-500 text-sm'}>Tracker</NavLink>
          <NavLink to="/about" className={({ isActive }) => isActive ? 'text-blue-600 text-sm' : 'text-gray-500 text-sm'}>About</NavLink>
        </div>

        <span className="text-gray-400 text-sm">Account</span>

      </div>
    </nav>
  )
}
