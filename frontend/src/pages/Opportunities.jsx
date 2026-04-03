import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import client from '../api/client'
import JobCard from '../components/JobCard'
import { useAuth } from '../context/AuthContext'

// Input box tailwind.css
const inputClass = 'border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

function getErrorMessage(error) {
  if (error.response?.status >= 500) {
    return 'The server had a problem loading opportunities. Try again in a moment.'
  }

  if (error.response?.status === 404) {
    return 'The opportunities service could not be found.'
  }

  if (error.code === 'ERR_NETWORK') {
    return 'Could not connect to the backend.' // Make sure the Flask API is running on port 5000.
  }

  return error.response?.data?.error || 'Something went wrong while loading opportunities.'
}

//Main component state
export default function Opportunities() {
  const { user } = useAuth()
  const [jobs, setJobs] = useState([])
  const [meta, setMeta] = useState({ page: 1, pages: 1, total: 0 })
  const [loading, setLoading] = useState(true) // Initial loading state
  const [isFetching, setIsFetching] = useState(false)
  const [error, setError] = useState('') // Current error message
  const [filters, setFilters] = useState({ keyword: '', company: '', location: '', role_type: '', sort: '' }) // Applied filters sent to API
  const [draftFilters, setDraftFilters] = useState({ keyword: '', company: '', location: '', role_type: '', sort: '' }) // Filters being edited by the user
  const [page, setPage] = useState(1)
  const [hasShownNoSkillsPrompt, setHasShownNoSkillsPrompt] = useState(false)

  useEffect(() => { // Timeout 350ms after user stops typing to apply filters, to avoid excessive API calls
    const timeoutId = setTimeout(() => {
      setFilters(draftFilters)
      setPage(1)
    }, 350)

    return () => clearTimeout(timeoutId)
  }, [draftFilters])

  useEffect(() => { // Fetch jobs when filters or page changes
    const fetchJobs = async () => {
      setIsFetching(true)
      setError('')
      try {
        const params = { page, per_page: 20, ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) }
        if (params.sort === 'match' && user?.id) {
          params.user_id = user.id
        }
        const { data } = await client.get('/jobs', { params })
        setJobs(data.results)
        setMeta({ page: data.page, pages: data.pages, total: data.total })
      } catch (err) {
        const message = getErrorMessage(err)
        setError(message)
        toast.error(`Error: ${message}`)
      } finally {
        setLoading(false)
        setIsFetching(false)
      }
    }
    fetchJobs()
  }, [filters, page])

  useEffect(() => {
    if (draftFilters.sort !== 'match') {
      setHasShownNoSkillsPrompt(false)
      return
    }

    if (!user?.id || hasShownNoSkillsPrompt) return

    const checkSkillsForMatchSort = async () => {
      try {
        const { data } = await client.get(`/profile/${user.id}`)
        const savedSkills = Array.isArray(data?.profile?.skills) ? data.profile.skills : []
        if (savedSkills.length === 0) {
          toast.error('Add skills in Settings to get "Most Relevant" matches.')
          setHasShownNoSkillsPrompt(true)
          setDraftFilters((prev) => ({ ...prev, sort: '' }))
        }
      } catch {
        // Ignore profile check errors and allow opportunities fetch to proceed normally.
      }
    }

    checkSkillsForMatchSort()
  }, [draftFilters.sort, user?.id, hasShownNoSkillsPrompt])

  const handleFilter = (e) => {
    setDraftFilters({ ...draftFilters, [e.target.name]: e.target.value })
  }

  const clearFilters = () => {
    const emptyFilters = { keyword: '', company: '', location: '', role_type: '', sort: '' }
    setDraftFilters(emptyFilters)
    setFilters(emptyFilters)
    setPage(1)
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">

      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Opportunities</h1>
          <p className="text-gray-500 text-sm">{meta.total} listings found</p>
        </div>
        {isFetching && !loading && (
          <p className="text-sm text-blue-600 bg-blue-50 border border-blue-100 rounded-full px-3 py-1">
            Updating results...
          </p>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6 items-center">
        <input className={inputClass} name="keyword" placeholder="Job title keyword" value={draftFilters.keyword} onChange={handleFilter} />
        <input className={inputClass} name="company" placeholder="Company" value={draftFilters.company} onChange={handleFilter} />
        <input className={inputClass} name="location" placeholder="Location" value={draftFilters.location} onChange={handleFilter} />
        <select className={inputClass} name="role_type" value={draftFilters.role_type} onChange={handleFilter}>
          <option value="">All role types</option>
          <option value="intern">Internship</option>
          <option value="graduate">Graduate</option>
          <option value="junior">Junior</option>
          <option value="placement">Placement</option>
        </select>
        <select className={inputClass} name="sort" value={draftFilters.sort} onChange={handleFilter}>
          <option value="">Sort by</option>
          <option value="deadline">Closing Deadline</option>
          <option value="match">Most Relevant</option>
          <option value="recent">Recently Opened</option>
        </select>
        <button
          type="button"
          onClick={clearFilters}
          className="text-sm px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Clear
        </button>
      </div>

      {/* Results */}
      {loading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : error && jobs.length === 0 ? (
        <p className="text-gray-400 text-sm">No listings match your filters right now.</p>
      ) : jobs.length === 0 ? (
        <p className="text-gray-400 text-sm">No listings match your filters.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {jobs.map(job => <JobCard key={job.id} job={job} />)}
        </div>
      )}

      {/* Pagination */}
      {meta.pages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-8">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="text-sm px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {page} of {meta.pages}</span>
          <button
            onClick={() => setPage(p => Math.min(meta.pages, p + 1))}
            disabled={page === meta.pages}
            className="text-sm px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}

    </div>
  )
}
