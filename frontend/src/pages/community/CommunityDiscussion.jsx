import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../../api/client'
import { useAuth } from '../../context/AuthContext'

export default function CommunityDiscussion() {
  const { user } = useAuth()
  const [threads, setThreads] = useState([])
  const [loadingThreads, setLoadingThreads] = useState(true)
  const [threadForm, setThreadForm] = useState({ title: '', content: '' })
  const [submittingThread, setSubmittingThread] = useState(false)

  const loadThreads = async () => {
    setLoadingThreads(true)
    try {
      const { data } = await api.get('/community/threads', {
        params: { category: 'discussion' },
      })
      setThreads(Array.isArray(data) ? data : [])
    } catch {
      toast.error('Error: Failed to load discussion threads.')
    } finally {
      setLoadingThreads(false)
    }
  }

  useEffect(() => {
    loadThreads()
  }, [])

  const submitThread = async (e) => {
    e.preventDefault()
    const title = threadForm.title.trim()
    const content = threadForm.content.trim()

    if (!user?.id) {
      toast.error('Error: You must be logged in to post.')
      return
    }
    if (!title || !content) {
      toast.error('Error: Title and content are required.')
      return
    }

    setSubmittingThread(true)
    try {
      const { data } = await api.post('/community/threads', {
        user_id: user.id,
        category: 'discussion',
        title,
        content,
      })

      setThreads((prev) => [data, ...prev])
      setThreadForm({ title: '', content: '' })
      toast.success('Thread created.')
    } catch (err) {
      const message = err?.response?.data?.error || 'Failed to create thread.'
      toast.error(`Error: ${message}`)
    } finally {
      setSubmittingThread(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <Link
        to="/community"
        className="inline-flex items-center pr-3 py-3 text-base font-medium text-blue-700 transition-colors hover:text-blue-900 hover:underline"
      >
        {'< Back to Community'}
      </Link>

      <h1 className="text-3xl font-bold text-slate-900">Community Discussion</h1>
      <p className="mt-2 text-slate-600">Start a thread and browse all discussion posts.</p>

      <section className="mt-6 bg-white border border-slate-200 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Start a thread</h2>

        <form onSubmit={submitThread} className="space-y-3">
          <input
            type="text"
            value={threadForm.title}
            onChange={(e) => setThreadForm((prev) => ({ ...prev, title: e.target.value }))}
            placeholder="Title"
            className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <textarea
            value={threadForm.content}
            onChange={(e) => setThreadForm((prev) => ({ ...prev, content: e.target.value }))}
            placeholder="What's on your mind?"
            rows={4}
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submittingThread}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
            >
              {submittingThread ? 'Posting...' : 'Post'}
            </button>
          </div>
        </form>
      </section>

      <section className="mt-6 space-y-4">
        {loadingThreads ? (
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-sm text-slate-500">Loading threads...</p>
          </div>
        ) : threads.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-sm text-slate-500">No threads yet. Start the first discussion.</p>
          </div>
        ) : (
          threads.map((thread) => (
            <article key={thread.id} className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="text-lg font-semibold text-slate-900">{thread.title}</h3>
              <p className="mt-1 text-xs text-slate-500">by {thread.author_username || 'Unknown'}</p>
              <p className="mt-3 text-sm text-slate-700 whitespace-pre-wrap">{thread.content}</p>
            </article>
          ))
        )}
      </section>
    </div>
  )
}
