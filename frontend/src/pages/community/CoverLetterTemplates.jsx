import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import trackerDevCoverLetter from '../../assets/cover-letter-templates/tracker.dev-cover-letter.docx'

export default function CoverLetterTemplates() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <Link
        to="/community"
        className="inline-flex items-center pr-3 py-3 text-base font-medium text-blue-700 transition-colors hover:text-blue-900 hover:underline"
      >
        {'< Back to Community'}
      </Link>

      <h1 className="text-3xl font-bold text-slate-900">Cover Letter Templates</h1>
      <p className="mt-2 text-slate-600">
        Download the tracker.dev cover letter template below. More cover letter templates are coming soon.
      </p>

      <section className="mt-6 bg-white border border-slate-200 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-900">Choose a template</h2>
        <p className="mt-1 text-sm text-slate-600">
          Click below to download the .docx cover letter template.
        </p>

        <div className="mt-5 flex flex-wrap gap-3">
          <a
            href={trackerDevCoverLetter}
            download="tracker.dev-cover-letter.docx"
            onClick={() => toast.success('Cover letter download started.')}
            className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Cover Letter
          </a>
        </div>
      </section>
    </div>
  )
}
