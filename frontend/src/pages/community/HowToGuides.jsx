import { Link } from 'react-router-dom'

export default function HowToGuides() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <Link
        to="/community"
        className="inline-flex items-center pr-3 py-3 text-base font-medium text-blue-700 transition-colors hover:text-blue-900 hover:underline"
      >
        {'< Back to Community'}
      </Link>

      <h1 className="text-3xl font-bold text-slate-900">How-To Guides</h1>
      <p className="mt-2 text-slate-600">Add practical step-by-step application guides here.</p>

      <section className="mt-6 bg-white border border-slate-200 rounded-xl p-6" />
    </div>
  )
}
