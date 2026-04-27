import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'

const inputClass = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
const labelClass = 'block text-sm font-medium text-gray-700 mb-1'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await client.post('/auth/login', form)
      login(data.user, data.token)
      toast.success('Logged in successfully.')
      navigate('/')
    } catch (err) {
      toast.error(`Error: ${err.response?.data?.error || 'Something went wrong'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 w-full max-w-md">

        {/* Brand */}
        <div className="flex justify-center mb-6">
          <div className="flex items-center gap-2 font-semibold text-gray-900">
            <span className="w-7 h-7 rounded bg-slate-800 text-white text-xs font-bold flex items-center justify-center">td</span>
            tracker.dev
          </div>
        </div>

        <h1 className="text-2xl font-bold text-gray-900 text-center mb-1">Welcome back</h1>
        <p className="text-gray-500 text-sm text-center mb-6">Log in to your tracker.dev account</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className={labelClass}>Username</label>
            <input type="text" name="username" value={form.username} onChange={handleChange} required className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Password</label>
            <input type="password" name="password" value={form.password} onChange={handleChange} required className={inputClass} />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white text-sm font-medium py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Logging in...' : 'Log in'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          Don't have an account?{' '}
          <Link to="/register" className="text-blue-600 hover:underline">Sign up</Link>
        </p>
      </div>
    </div>
  )
}

