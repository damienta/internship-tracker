import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import client from '../api/client'
import JobCard from '../components/JobCard'
import DeadlineJobCard from '../components/DeadlineJobCard'

function parseDate(value) {
  if (!value) return null
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return null
  d.setHours(0, 0, 0, 0)
  return d
}

function daysUntil(dateString) {
  const d = parseDate(dateString)
  if (!d) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diffMs = d - today
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24))
}

function isUpcomingDeadline(deadline) {
  const d = parseDate(deadline)
  if (!d) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return d >= today
}

export default function Home() {
  const [recentJobs, setRecentJobs] = useState([])
  const [deadlineJobs, setDeadlineJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchJobs = async () => {
      setLoading(true)
      try {
        const [recentRes, deadlineRes] = await Promise.all([
          client.get('/jobs', { params: { page: 1, per_page: 100, sort: 'scraped' } }),
          client.get('/jobs/upcoming', { params: { limit: 3 } }),
        ])

        const recentResults = Array.isArray(recentRes?.data?.results) ? recentRes.data.results : []
        const deadlineResults = Array.isArray(deadlineRes?.data?.results) ? deadlineRes.data.results : []

        setRecentJobs(recentResults)
        setDeadlineJobs(deadlineResults)
      } catch {
        toast.error('Error: Could not load home dashboard data.')
      } finally {
        setLoading(false)
      }
    }

    fetchJobs()
  }, [])

  const topRecent = useMemo(() => recentJobs.slice(0, 10), [recentJobs])

  const upcomingDeadlines = useMemo(() => {
    return deadlineJobs
      .filter((job) => isUpcomingDeadline(job.deadline))
      .sort((a, b) => parseDate(a.deadline) - parseDate(b.deadline))
      .slice(0, 3)
  }, [deadlineJobs])

  const newThisWeek = useMemo(() => {
    const now = new Date()
    const weekAgo = new Date(now)
    weekAgo.setDate(now.getDate() - 7)

    return recentJobs.filter((job) => {
      if (!job.scraped_at) return false
      const scrapedAt = new Date(job.scraped_at)
      return scrapedAt >= weekAgo
    }).length
  }, [recentJobs])

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Home</h1>
        <p className="text-gray-500 text-sm">Top opportunities and quick deadline tracking.</p>
      </div>

      {loading ? (
        <p className="text-gray-500 text-sm">Loading dashboard...</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <section className="lg:col-span-2">
            <div className="mb-3">
              <h2 className="font-semibold text-gray-900">Recent Opportunities</h2>
            </div>

            <div className="flex flex-col gap-3">
              {topRecent.length === 0 ? (
                <p className="text-sm text-gray-500">No recent opportunities available.</p>
              ) : (
                topRecent.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))
              )}
            </div>
          </section>

          <aside className="space-y-4">
            <div className="bg-white border border-gray-200 rounded-2xl p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Upcoming Deadlines</h3>

              {upcomingDeadlines.length === 0 ? (
                <p className="text-sm text-gray-500">No upcoming deadlines found.</p>
              ) : (
                <div className="flex flex-col gap-3">
                  {upcomingDeadlines.map((job) => {
                    const daysLeft = daysUntil(job.deadline)
                    return (
                      <DeadlineJobCard key={`deadline-${job.id}`} job={job} daysLeft={daysLeft} />
                    )
                  })}
                </div>
              )}
            </div>

            <div className="bg-white border border-gray-200 rounded-2xl p-4">
              <h3 className="font-semibold text-gray-900">New This Week</h3>
              <p className="text-3xl font-bold text-blue-700 mt-2">{newThisWeek}</p>
              <p className="text-xs text-gray-500 mt-1">Opportunities scraped in the last 7 days.</p>
            </div>
          </aside>
        </div>
      )}
    </div>
  )
}
