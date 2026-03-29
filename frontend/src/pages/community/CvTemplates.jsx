import { Link } from 'react-router-dom'
import technicalCvTemplate from '../../assets/cv-templates/Tracker.dev-Techncial-CV-Template-.docx'
import nonTechnicalCvTemplate from '../../assets/cv-templates/Tracker.dev-Non-Techncial-CV-Template-.docx'

export default function CvTemplates() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <Link
        to="/community"
        className="inline-flex items-center pr-3 py-3 text-base font-medium text-blue-700 transition-colors hover:text-blue-900 hover:underline"
      >
        {'< Back to Community'}
      </Link>

      <h1 className="text-3xl font-bold text-slate-900">CV Templates</h1>
      <p className="mt-2 text-slate-600">
        Download a ready-to-edit CV template in Word format based on the role type you are applying for.
      </p>

      <section className="mt-6 bg-white border border-slate-200 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-900">Choose a template</h2>
        <p className="mt-1 text-sm text-slate-600">
          Click a button below to download a .docx template directly.
        </p>

        <div className="mt-5 flex flex-wrap gap-3">
          <a
            href={technicalCvTemplate}
            download="tracker.dev-technical-cv-template.docx"
            className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Technical CV
          </a>

          <a
            href={nonTechnicalCvTemplate}
            download="tracker.dev-non-technical-cv-template.docx"
            className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Non-Technical CV
          </a>
        </div>
      </section>
    </div>
  )
}
