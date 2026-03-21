import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

const PAGE_SIZE = 10

const STATUS_OPTIONS = [
  'Applied',
  'Phone Screening',
  'Recruiter Call',
  'First Interview',
  'Second Interview',
  'Accepted',
  'Rejected'
]

const inputClass = 'w-full border border-gray-300 rounded-lg px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500'
const fieldLabelClass = 'block text-xs font-semibold tracking-wide text-gray-600 uppercase mb-1'

function getApiErrorMessage(err, fallback) {
  return err?.response?.data?.error || fallback
}

function isValidDateString(value) {
  if (!value) return true
  const isoDate = /^\d{4}-\d{2}-\d{2}$/
  if (!isoDate.test(value)) return false
  const date = new Date(value)
  return !Number.isNaN(date.getTime())
}

function isValidLink(value) {
  if (!value) return false
  return value.startsWith('http://') || value.startsWith('https://')
}

export default function Tracker() {
  const { user } = useAuth()
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [page, setPage] = useState(1)
  const [showAddForm, setShowAddForm] = useState(false)
  const [form, setForm] = useState({
    status: 'Applied',
    company: '',
    role: '',
    opening_date: '',
    closing_date: '',
    link: '',
    notes: '',
  })

  useEffect(() => {
    if (!user?.id) {
      setEntries([])
      setLoading(false)
      setError('Please log in to use the tracker.')
      return
    }

    const fetchEntries = async () => {
      setLoading(true)
      setError('')
      try {
        const { data } = await api.get('/tracker', { params: { user_id: user.id } })
        setEntries(Array.isArray(data) ? data : [])
      } catch {
        setError('Failed to load tracker entries.')
      } finally {
        setLoading(false)
      }
    }

    fetchEntries()
  }, [user?.id])

  const filtered = useMemo(() => entries, [entries])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages)
    }
  }, [page, totalPages])

  const pagedEntries = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE
    return filtered.slice(start, start + PAGE_SIZE)
  }, [filtered, page])

  const handleEntryChange = (id, field, value) => {
    setEntries((prev) =>
      prev.map((entry) => (entry.id === id ? { ...entry, [field]: value } : entry))
    )
  }

  const saveField = async (id, field, value) => {
    if (!user?.id) return

    const current = entries.find((entry) => entry.id === id)
    if (current) {
      const company = field === 'company' ? String(value || '').trim() : String(current.company || '').trim()
      const role = field === 'role' ? String(value || '').trim() : String(current.role || '').trim()
      const link = field === 'link' ? String(value || '').trim() : String(current.link || '').trim()
      const openingDate = field === 'opening_date' ? (value || null) : current.opening_date
      const closingDate = field === 'closing_date' ? (value || null) : current.closing_date

      if (!isValidLink(link)) {
        const msg = 'Link must start with http:// or https://.'
        setError(msg)
        toast.error(`Error: ${msg}`)
        return
      }

      if (!isValidDateString(openingDate) || !isValidDateString(closingDate)) {
        const msg = 'Dates must be valid.'
        setError(msg)
        toast.error(`Error: ${msg}`)
        return
      }

      if (openingDate && closingDate && closingDate < openingDate) {
        const msg = 'Closing date cannot be earlier than opening date.'
        setError(msg)
        toast.error(`Error: ${msg}`)
        return
      }
    }

    setError('')
    try {
      await api.patch(`/tracker/${id}`, { user_id: user.id, [field]: value })
      toast.success('Update saved.')
    } catch (err) {
      const msg = getApiErrorMessage(err, 'Failed to save changes. Please try again.')
      setError(msg)
      toast.error(`Error: ${msg}`)
    }
  }

  const handleFormChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleAddEntry = async (e) => {
    e.preventDefault()

    if (!form.company.trim() || !form.role.trim() || !form.link.trim()) {
      const msg = 'Company, role and link are required.'
      setError(msg)
      toast.error(`Error: ${msg}`)
      return
    }

    if (!isValidLink(form.link.trim())) {
      const msg = 'Link must start with http:// or https://.'
      setError(msg)
      toast.error(`Error: ${msg}`)
      return
    }

    if (!isValidDateString(form.opening_date) || !isValidDateString(form.closing_date)) {
      const msg = 'Dates must be valid.'
      setError(msg)
      toast.error(`Error: ${msg}`)
      return
    }

    if (form.opening_date && form.closing_date && form.closing_date < form.opening_date) {
      const msg = 'Closing date cannot be earlier than opening date.'
      setError(msg)
      toast.error(`Error: ${msg}`)
      return
    }

    const payload = {
      user_id: user?.id,
      status: form.status,
      company: form.company.trim(),
      role: form.role.trim(),
      opening_date: form.opening_date || null,
      closing_date: form.closing_date || null,
      link: form.link.trim(),
      notes: form.notes.trim(),
    }

    setError('')
    try {
      const { data } = await api.post('/tracker', payload)
      setEntries((prev) => [data, ...prev])
      setForm({
        status: 'Applied',
        company: '',
        role: '',
        opening_date: '',
        closing_date: '',
        link: '',
        notes: '',
      })
      setShowAddForm(false)
      setPage(1)
      toast.success('Application added.')
    } catch (err) {
      const msg = getApiErrorMessage(err, 'Failed to save tracker entry. Check backend/database and try again.')
      setError(msg)
      toast.error(`Error: ${msg}`)
    }
  }

  const handleDelete = async (id) => {
    if (!user?.id) return
    setError('')
    try {
      await api.delete(`/tracker/${id}`, { params: { user_id: user.id } })
      setEntries((prev) => prev.filter((entry) => entry.id !== id))
      toast.success('Application deleted.')
    } catch (err) {
      const msg = getApiErrorMessage(err, 'Failed to delete entry. Please try again.')
      setError(msg)
      toast.error(`Error: ${msg}`)
    }
  }

  return (
    <div className="w-full px-4 md:px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Tracker</h1>
        <p className="text-gray-500 text-sm">Status can be updated for saved entries.</p>
      </div>

      <div className="mb-4 flex justify-start">
        <button
          type="button"
          onClick={() => setShowAddForm((v) => !v)}
          className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Add Application
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleAddEntry} className="bg-white border border-gray-200 rounded-xl p-5 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <div>
              <label className={fieldLabelClass}>Status</label>
              <select name="status" value={form.status} onChange={handleFormChange} className={inputClass}>
                {STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>

            <div>
              <label className={fieldLabelClass}>Company Name</label>
              <input name="company" value={form.company} onChange={handleFormChange} placeholder="e.g BT" className={inputClass} required />
            </div>

            <div>
              <label className={fieldLabelClass}>Role</label>
              <input name="role" value={form.role} onChange={handleFormChange} placeholder="e.g Software Engineering Intern" className={inputClass} required />
            </div>

            <div>
              <label className={fieldLabelClass}>Opening Date</label>
              <input type="date" name="opening_date" value={form.opening_date} onChange={handleFormChange} className={inputClass} />
            </div>

            <div>
              <label className={fieldLabelClass}>Closing Date</label>
              <input type="date" name="closing_date" value={form.closing_date} onChange={handleFormChange} className={inputClass} />
            </div>

            <div>
              <label className={fieldLabelClass}>Link</label>
              <input type="url" name="link" value={form.link} onChange={handleFormChange} placeholder="e.g https://example.com" className={inputClass} required />
            </div>

            <div className="md:col-span-2 lg:col-span-3">
              <label className={fieldLabelClass}>Notes</label>
              <input name="notes" value={form.notes} onChange={handleFormChange} placeholder="Add any additional notes" className={inputClass} />
            </div>
          </div>

          <div className="mt-4 pt-3 flex justify-center gap-3">
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="text-sm px-2 py-1 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button type="submit" className="bg-blue-600 text-white text-sm px-2 py-1 rounded-lg hover:bg-blue-700">
              Save
            </button>
          </div>
        </form>
      )}

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="px-4 py-6 text-sm text-gray-500">Loading tracker entries...</div>
        ) : (
        <table className="w-full table-fixed text-xs">
          <thead className="bg-gray-50 text-gray-700">
            <tr>
              <th className="text-left px-2 py-2 font-semibold w-[13%]">Status</th>
              <th className="text-left px-2 py-2 font-semibold w-[14%]">Company Name</th>
              <th className="text-left px-2 py-2 font-semibold w-[14%]">Role</th>
              <th className="text-left px-2 py-2 font-semibold w-[13%]">Opening Date</th>
              <th className="text-left px-2 py-2 font-semibold w-[13%]">Closing Date</th>
              <th className="text-left px-2 py-2 font-semibold w-[15%]">Link</th>
              <th className="text-left px-2 py-2 font-semibold w-[18%]">Notes</th>
            </tr>
          </thead>
          <tbody>
            {pagedEntries.length === 0 ? (
              <tr>
                <td className="px-3 py-6 text-gray-500" colSpan={7}>No Tracker Entries Yet.</td>
              </tr>
            ) : (
              pagedEntries.map((entry) => (
                <tr key={entry.id} className="group border-t border-gray-100">
                  <td className="px-2 py-2 align-top">
                    <select
                      value={entry.status}
                      onChange={(e) => {
                        const value = e.target.value
                        handleEntryChange(entry.id, 'status', value)
                        saveField(entry.id, 'status', value)
                      }}
                      className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
                    >
                      {STATUS_OPTIONS.map((status) => (
                        <option key={status} value={status}>{status}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-2 py-2 text-gray-800 align-top">
                    <input
                      value={entry.company || ''}
                      onChange={(e) => handleEntryChange(entry.id, 'company', e.target.value)}
                      onBlur={(e) => saveField(entry.id, 'company', e.target.value)}
                      className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="px-2 py-2 text-gray-700 align-top">
                    <input
                      value={entry.role || ''}
                      onChange={(e) => handleEntryChange(entry.id, 'role', e.target.value)}
                      onBlur={(e) => saveField(entry.id, 'role', e.target.value)}
                      className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="px-2 py-2 text-gray-600 align-top">
                    <input
                      type="date"
                      value={entry.opening_date || ''}
                      onChange={(e) => handleEntryChange(entry.id, 'opening_date', e.target.value || null)}
                      onBlur={(e) => saveField(entry.id, 'opening_date', e.target.value || null)}
                      className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="px-2 py-2 text-gray-600 align-top">
                    <input
                      type="date"
                      value={entry.closing_date || ''}
                      onChange={(e) => handleEntryChange(entry.id, 'closing_date', e.target.value || null)}
                      onBlur={(e) => saveField(entry.id, 'closing_date', e.target.value || null)}
                      className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="px-2 py-2 text-gray-600 align-top">
                    <input
                      type="url"
                      value={entry.link || ''}
                      onChange={(e) => handleEntryChange(entry.id, 'link', e.target.value)}
                      onBlur={(e) => saveField(entry.id, 'link', e.target.value)}
                      className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
                      placeholder="e.g https://..."
                    />
                  </td>
                  <td className="px-2 py-2 text-gray-600 align-top">
                    <div className="flex items-center gap-1">
                      <input
                        value={entry.notes || ''}
                        onChange={(e) => handleEntryChange(entry.id, 'notes', e.target.value)}
                        onBlur={(e) => saveField(entry.id, 'notes', e.target.value)}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
                      />
                      <button
                        type="button"
                        onClick={() => handleDelete(entry.id)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity border border-red-200 text-red-600 rounded px-2 py-1 text-xs hover:bg-red-50"
                        aria-label="Delete entry"
                        title="Delete"
                      >
                        Bin
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        )}
      </div>

      <div className="mt-5 flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="text-sm px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
        >
          Previous
        </button>

        <span className="text-sm text-gray-500">Page {page} of {totalPages}</span>

        <button
          type="button"
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page === totalPages}
          className="text-sm px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  )
}
