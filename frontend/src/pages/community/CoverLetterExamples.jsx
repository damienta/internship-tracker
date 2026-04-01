import { Link } from 'react-router-dom'

export default function CoverLetterExamples() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <Link
        to="/community"
        className="inline-flex items-center pr-3 py-3 text-base font-medium text-blue-700 transition-colors hover:text-blue-900 hover:underline"
      >
        {'< Back to Community'}
      </Link>

      <h1 className="text-3xl font-bold text-slate-900">Cover Letter Examples</h1>
      <p className="mt-2 text-slate-600">
        Explore cover letter examples and discuss which structures and tones work best for different companies.
      </p>

      <section className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <article className="bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-slate-900">Example 1</h2>
          <p className="mt-2 text-sm text-slate-600">Add your first cover letter example here.</p>
        </article>

        <article className="bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-slate-900">Example 2</h2>
          <p className="mt-2 text-sm text-slate-600">Add your second cover letter example here.</p>
        </article>
      </section>
    </div>
  )
}
