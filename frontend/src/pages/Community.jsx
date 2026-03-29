import { Link } from 'react-router-dom'

export default function Community() {
  const sections = [
    {
      title: 'CV Templates',
      path: '/community/cv-templates',
      description: 'Browse CV template options for different application styles.',
    },
    {
      title: 'CV Examples',
      path: '/community/cv-examples',
      description: 'See example CVs and what makes each one effective.',
    },
    {
      title: 'Cover Letter Templates',
      path: '/community/cover-letter-templates',
      description: 'Use starter cover letter formats for different tones and roles.',
    },
    {
      title: 'How-To Guides',
      path: '/community/how-to-guides',
      description: 'Follow step-by-step guides for research, interviews, and follow-up.',
    },
    {
      title: 'Company Ratings',
      path: '/community/company-ratings',
      description: 'View structured company feedback based on candidate experience.',
    },
    {
      title: 'Community Discussion',
      path: '/community/discussion',
      description: 'Community discussion (add peer tips): users can add a thread.',
    },
  ]

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold text-slate-900">Community</h1>
      <p className="mt-2 text-sm text-slate-600">
        Community and career toolkit hub.
      </p>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        {sections.map((section) => (
          <Link
            key={section.path}
            to={section.path}
            className="block bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-300 hover:bg-slate-50"
          >
            <h2 className="text-lg font-semibold text-slate-900">{section.title}</h2>
            <p className="mt-2 text-sm text-slate-700 leading-relaxed">{section.description}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
