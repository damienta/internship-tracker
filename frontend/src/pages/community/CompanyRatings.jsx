import { Link } from 'react-router-dom'

export default function CompanyRatings() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold text-slate-900">Company Ratings</h1>
      <p className="mt-2 text-slate-600">Add your structured company rating model and feedback here.</p>

      <section className="mt-6 bg-white border border-slate-200 rounded-xl p-6" />

      <Link to="/community" className="inline-block mt-6 text-sm text-blue-700 hover:text-blue-800">Back to Community</Link>
    </div>
  )
}
