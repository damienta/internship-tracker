import { useState, useEffect } from 'react'
import client from '../api/client'
import locationIcon from '../assets/location.png'

// Input box tailwind.css
const inputClass = 'border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

const SOURCE_LABELS = {
  lever:      'Lever',
  greenhouse: 'Greenhouse',
  ashby:      'Ashby',
  bt:         'BT',
  hsbc:       'HSBC',
  sap:        'SAP',
}

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

function JobCard({ job }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 flex flex-col gap-2">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-semibold text-gray-900 text-base">{job.title}</h2>
          <p className="text-gray-500 text-sm">{job.company}</p>
        </div>
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 text-sm bg-blue-600 text-white px-4 py-1.5 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Apply
        </a>
      </div>
      <div className="flex flex-wrap gap-2 text-xs text-gray-500">
        {job.location && (
          <span className="inline-flex items-center gap-1">
            <img src={locationIcon} alt="" className="w-4 h-4 opacity-70" />
            {job.location}
          </span>
        )}
        {job.source_website && <span className="bg-gray-100 px-2 py-0.5 rounded">{SOURCE_LABELS[job.source_website] ?? job.source_website}</span>}
      </div>
      {job.extracted_skills?.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {job.extracted_skills.slice(0, 6).map(skill => (
            <span key={skill} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">{skill}</span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Opportunities() {
  const [jobs, setJobs] = useState([])
  const [meta, setMeta] = useState({ page: 1, pages: 1, total: 0 })
  const [loading, setLoading] = useState(true)
  const [isFetching, setIsFetching] = useState(false)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({ keyword: '', company: '', location: '', role_type: '' })
  const [draftFilters, setDraftFilters] = useState({ keyword: '', company: '', location: '', role_type: '' })
  const [page, setPage] = useState(1)

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setFilters(draftFilters)
      setPage(1)
    }, 350)

    return () => clearTimeout(timeoutId)
  }, [draftFilters])

  useEffect(() => {
    const fetchJobs = async () => {
      setIsFetching(true)
      setError('')
      try {
        const params = { page, per_page: 20, ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) }
        const { data } = await client.get('/jobs', { params })
        setJobs(data.results)
        setMeta({ page: data.page, pages: data.pages, total: data.total })
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        setLoading(false)
        setIsFetching(false)
      }
    }
    fetchJobs()
  }, [filters, page])

  const handleFilter = (e) => {
    setDraftFilters({ ...draftFilters, [e.target.name]: e.target.value })
  }

  const clearFilters = () => {
    const emptyFilters = { keyword: '', company: '', location: '', role_type: '' }
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

      {error && jobs.length > 0 && (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
          <p className="text-sm text-amber-800">{error}</p>
        </div>
      )}

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
        <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-6">
          <p className="text-sm font-medium text-red-800 mb-2">Could not load opportunities.</p>
          <p className="text-sm text-red-700">{error}</p>
        </div>
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
