import { Link } from 'react-router-dom'

export default function Community() {
  const sections = [
    {
      title: 'CV Templates and Examples',
      path: '/community/cv-templates',
      description: 'Download the CV template, review the example CVs, understand what the company you are applying to is looking for and fill in the gaps with your experience.',
    },
    {
      title: 'Cover Letter Templates and Examples',
      path: '/community/cover-letter-templates',
      description: 'Download the cover letter template, review the example cover letters, understand what the company you are applying to is looking for and fill in the gaps.',
    },
    {
      title: 'How-To Guides',
      path: '/community/how-to-guides',
      description: 'Follow step-by-step guidance for applications, interviews, how to write a CV, how to write a cover letter and follow-ups, with tips you can test and discuss by company in the forum.',
    },
    {
      title: 'Community Discussion',
      path: '/community/discussion',
      description: 'Join open discussions to share tips for anything related to career development, ask questions, and discuss company application experiences all in one place.',
    },
  ]

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold text-slate-900">Community</h1>
      <p className="mt-2 text-sm text-slate-600">
        Community and career toolkit hub for templates, examples, and company-focused discussion.
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
