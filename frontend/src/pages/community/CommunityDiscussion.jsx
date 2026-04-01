import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../../api/client'
import { useAuth } from '../../context/AuthContext'

export default function CommunityDiscussion() {
  const { user } = useAuth()
  const [threads, setThreads] = useState([])
  const [loadingThreads, setLoadingThreads] = useState(true)
  const [expandedThreadIds, setExpandedThreadIds] = useState([])
  const [repliesByThread, setRepliesByThread] = useState({})
  const [loadingRepliesByThread, setLoadingRepliesByThread] = useState({})

  const [threadForm, setThreadForm] = useState({ title: '', content: '' })
  const [replyTextByThread, setReplyTextByThread] = useState({})
  const [editingThreadId, setEditingThreadId] = useState(null)
  const [editThreadForm, setEditThreadForm] = useState({ title: '', content: '' })
  const [editingReplyId, setEditingReplyId] = useState(null)
  const [editReplyText, setEditReplyText] = useState('')
  const [submittingThread, setSubmittingThread] = useState(false)
  const [submittingReplyThreadId, setSubmittingReplyThreadId] = useState(null)

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

  const loadReplies = async (threadId) => {
    if (!threadId) return

    setLoadingRepliesByThread((prev) => ({ ...prev, [threadId]: true }))
    try {
      const { data } = await api.get(`/community/threads/${threadId}/replies`)
      setRepliesByThread((prev) => ({
        ...prev,
        [threadId]: Array.isArray(data) ? data : [],
      }))
    } catch {
      toast.error('Error: Failed to load replies.')
    } finally {
      setLoadingRepliesByThread((prev) => ({ ...prev, [threadId]: false }))
    }
  }

  const toggleReplies = async (threadId) => {
    const isExpanded = expandedThreadIds.includes(threadId)
    if (isExpanded) {
      setExpandedThreadIds((prev) => prev.filter((id) => id !== threadId))
      return
    }

    setExpandedThreadIds((prev) => [...prev, threadId])
    if (!repliesByThread[threadId]) {
      await loadReplies(threadId)
    }
  }

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
      setExpandedThreadIds((prev) => (prev.includes(data.id) ? prev : [data.id, ...prev]))
      toast.success('Thread created.')
    } catch (err) {
      const message = err?.response?.data?.error || 'Failed to create thread.'
      toast.error(`Error: ${message}`)
    } finally {
      setSubmittingThread(false)
    }
  }

  const submitReply = async (threadId) => {
    const content = String(replyTextByThread[threadId] || '').trim()

    if (!user?.id) {
      toast.error('Error: You must be logged in to reply.')
      return
    }
    if (!content) {
      toast.error('Error: Reply cannot be empty.')
      return
    }

    setSubmittingReplyThreadId(threadId)
    try {
      const { data } = await api.post(`/community/threads/${threadId}/replies`, {
        user_id: user.id,
        content,
      })

      setRepliesByThread((prev) => {
        const existing = Array.isArray(prev[threadId]) ? prev[threadId] : []
        return { ...prev, [threadId]: [...existing, data] }
      })
      setReplyTextByThread((prev) => ({ ...prev, [threadId]: '' }))
      setExpandedThreadIds((prev) => (prev.includes(threadId) ? prev : [...prev, threadId]))

      setThreads((prev) => {
        const idx = prev.findIndex((thread) => thread.id === threadId)
        if (idx <= 0) return prev
        const next = [...prev]
        const [active] = next.splice(idx, 1)
        next.unshift(active)
        return next
      })

      toast.success('Reply posted.')
    } catch (err) {
      const message = err?.response?.data?.error || 'Failed to post reply.'
      toast.error(`Error: ${message}`)
    } finally {
      setSubmittingReplyThreadId(null)
    }
  }

  const deleteThread = async (threadId) => {
    if (!user?.id) {
      toast.error('Error: You must be logged in to delete a thread.')
      return
    }

    try {
      await api.delete(`/community/threads/${threadId}`, {
        params: { user_id: user.id },
      })

      setThreads((prev) => prev.filter((thread) => thread.id !== threadId))
      setExpandedThreadIds((prev) => prev.filter((id) => id !== threadId))
      setRepliesByThread((prev) => {
        const next = { ...prev }
        delete next[threadId]
        return next
      })
      toast.success('Thread deleted.')
    } catch (err) {
      const message = err?.response?.data?.error || 'Failed to delete thread.'
      toast.error(`Error: ${message}`)
    }
  }

  const startEditThread = (thread) => {
    setEditingThreadId(thread.id)
    setEditThreadForm({ title: thread.title || '', content: thread.content || '' })
  }

  const saveEditThread = async (threadId) => {
    const title = editThreadForm.title.trim()
    const content = editThreadForm.content.trim()

    if (!user?.id) {
      toast.error('Error: You must be logged in to edit a thread.')
      return
    }
    if (!title || !content) {
      toast.error('Error: Title and content are required.')
      return
    }

    try {
      const { data } = await api.patch(`/community/threads/${threadId}`, {
        user_id: user.id,
        title,
        content,
      })

      setThreads((prev) => prev.map((thread) => (thread.id === threadId ? data : thread)))
      setEditingThreadId(null)
      setEditThreadForm({ title: '', content: '' })
      toast.success('Thread updated.')
    } catch (err) {
      const message = err?.response?.data?.error || 'Failed to update thread.'
      toast.error(`Error: ${message}`)
    }
  }

  const startEditReply = (reply) => {
    setEditingReplyId(reply.id)
    setEditReplyText(reply.content || '')
  }

  const saveEditReply = async (threadId, replyId) => {
    const content = editReplyText.trim()
    if (!user?.id) {
      toast.error('Error: You must be logged in to edit a reply.')
      return
    }
    if (!content) {
      toast.error('Error: Reply cannot be empty.')
      return
    }

    try {
      const { data } = await api.patch(`/community/replies/${replyId}`, {
        user_id: user.id,
        content,
      })

      setRepliesByThread((prev) => ({
        ...prev,
        [threadId]: (prev[threadId] || []).map((reply) => (reply.id === replyId ? data : reply)),
      }))
      setEditingReplyId(null)
      setEditReplyText('')
      toast.success('Reply updated.')
    } catch (err) {
      const message = err?.response?.data?.error || 'Failed to update reply.'
      toast.error(`Error: ${message}`)
    }
  }

  const deleteReply = async (threadId, replyId) => {
    if (!user?.id) {
      toast.error('Error: You must be logged in to delete a reply.')
      return
    }

    try {
      await api.delete(`/community/replies/${replyId}`, {
        params: { user_id: user.id },
      })
      setRepliesByThread((prev) => ({
        ...prev,
        [threadId]: (prev[threadId] || []).filter((reply) => reply.id !== replyId),
      }))
      toast.success('Reply deleted.')
    } catch (err) {
      const message = err?.response?.data?.error || 'Failed to delete reply.'
      toast.error(`Error: ${message}`)
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
          threads.map((thread) => {
            const isExpanded = expandedThreadIds.includes(thread.id)
            const replies = repliesByThread[thread.id] || []
            const isLoadingReplies = loadingRepliesByThread[thread.id]

            return (
              <article
                key={thread.id}
                className="bg-white border border-slate-200 rounded-xl p-5 cursor-pointer"
                onClick={() => toggleReplies(thread.id)}
              >
                <div className="flex items-start justify-between gap-4">
                  {editingThreadId === thread.id ? (
                    <div className="w-full space-y-2">
                      <input
                        type="text"
                        value={editThreadForm.title}
                        onChange={(e) => setEditThreadForm((prev) => ({ ...prev, title: e.target.value }))}
                        onClick={(e) => e.stopPropagation()}
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <textarea
                        value={editThreadForm.content}
                        onChange={(e) => setEditThreadForm((prev) => ({ ...prev, content: e.target.value }))}
                        onClick={(e) => e.stopPropagation()}
                        rows={4}
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => saveEditThread(thread.id)}
                          onMouseDown={(e) => e.stopPropagation()}
                          className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setEditingThreadId(null)
                            setEditThreadForm({ title: '', content: '' })
                          }}
                          onMouseDown={(e) => e.stopPropagation()}
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleReplies(thread.id)
                      }}
                      className="text-left"
                    >
                      <h3 className="text-lg font-semibold text-slate-900 hover:text-blue-700">{thread.title}</h3>
                      <p className="mt-1 text-xs text-slate-500">by {thread.author_username || 'Unknown'}</p>
                    </button>
                  )}

                  {user?.id === thread.user_id ? (
                    <div className="flex gap-2">
                      {editingThreadId !== thread.id ? (
                        <button
                          type="button"
                          onClick={() => startEditThread(thread)}
                          onMouseDown={(e) => e.stopPropagation()}
                          className="rounded-lg border border-blue-200 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50"
                        >
                          Edit
                        </button>
                      ) : null}
                      <button
                        type="button"
                        onClick={() => deleteThread(thread.id)}
                        onMouseDown={(e) => e.stopPropagation()}
                        className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50"
                      >
                        Delete
                      </button>
                    </div>
                  ) : null}
                </div>

                {editingThreadId !== thread.id ? (
                  <p className="mt-3 text-sm text-slate-700 whitespace-pre-wrap">{thread.content}</p>
                ) : null}
                {isExpanded ? (
                  <div className="mt-3 border-t border-slate-200 pt-3">
                    <p className="mb-3 text-sm font-semibold text-slate-700">Replies ({replies.length})</p>

                    {isLoadingReplies ? (
                      <p className="text-sm text-slate-500">Loading replies...</p>
                    ) : replies.length === 0 ? (
                      <p className="text-sm text-slate-500">No replies yet.</p>
                    ) : (
                      <ul className="space-y-3">
                        {replies.map((reply) => (
                          <li key={reply.id} className="rounded-lg border border-slate-200 p-3">
                            <div className="flex items-start justify-between gap-3">
                              <p className="text-xs text-slate-500">Reply by {reply.author_username || 'Unknown'}</p>
                              {user?.id === reply.user_id ? (
                                <div className="flex gap-2">
                                  {editingReplyId !== reply.id ? (
                                    <button
                                      type="button"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        startEditReply(reply)
                                      }}
                                      onMouseDown={(e) => e.stopPropagation()}
                                      className="rounded-lg border border-blue-200 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50"
                                    >
                                      Edit
                                    </button>
                                  ) : null}
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      deleteReply(thread.id, reply.id)
                                    }}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50"
                                  >
                                    Delete
                                  </button>
                                </div>
                              ) : null}
                            </div>

                            {editingReplyId === reply.id ? (
                              <div className="mt-2 space-y-2">
                                <textarea
                                  value={editReplyText}
                                  onChange={(e) => setEditReplyText(e.target.value)}
                                  onClick={(e) => e.stopPropagation()}
                                  rows={3}
                                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <div className="flex gap-2">
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      saveEditReply(thread.id, reply.id)
                                    }}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
                                  >
                                    Save
                                  </button>
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      setEditingReplyId(null)
                                      setEditReplyText('')
                                    }}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <p className="text-sm text-slate-700 whitespace-pre-wrap">{reply.content}</p>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}

                    <div className="mt-4 space-y-2">
                      <textarea
                        value={replyTextByThread[thread.id] || ''}
                        onChange={(e) => setReplyTextByThread((prev) => ({ ...prev, [thread.id]: e.target.value }))}
                        onClick={(e) => e.stopPropagation()}
                        rows={3}
                        placeholder="Write your reply"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        type="button"
                        onClick={() => submitReply(thread.id)}
                        onMouseDown={(e) => e.stopPropagation()}
                        disabled={submittingReplyThreadId === thread.id}
                        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
                      >
                        {submittingReplyThreadId === thread.id ? 'Posting...' : 'Post Reply'}
                      </button>
                    </div>
                  </div>
                ) : null}
              </article>
            )
          })
        )}
      </section>
    </div>
  )
}
