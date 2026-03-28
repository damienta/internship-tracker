export default function About() {
  const recommendedSites = [
    {
      name: 'Trackr',
      url: 'https://the-trackr.com/',
      description: 'Track applications and keep your pipeline organized across companies.',
    },
    {
      name: 'Bright Network',
      url: 'https://www.brightnetwork.co.uk',
      description: 'Student and graduate opportunities, events, and practical career resources.',
    },
    {
      name: 'Jack and Jill Jobs',
      url: 'https://www.jackandjill.ai/',
      description: 'UK-focused graduate and internship listings with early-career filters.',
    },
  ]

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold text-slate-900">About</h1>

      <section className="mt-6 bg-white border border-slate-200 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-slate-900">What tracker.dev does</h2>
        <p className="mt-3 text-slate-700 leading-relaxed">
          tracker.dev is built to help student, early-career and junior applicants manage job applications more effectively
          by providing a centralised platform for all their needs. tracker.dev combines opportunity discovery, application tracking,
          and deadline visibility so users do not need to switch between spreadsheets, job boards, and different websites.
        </p>
      </section>

      <section className="mt-5 bg-white border border-slate-200 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-slate-900">How tracker.dev helps</h2>
        <ul className="mt-3 space-y-2 text-slate-700 list-disc pl-5">
          <li>Finds and displays current opportunities all in one dashboard.</li>
          <li>Tracks progress across application stages in a structured way.</li>
          <li>Gives you personalised CV reviews and CV templates to use for your job applications.</li>
          <li>Spots upcoming deadlines early to avoid missing application windows.</li>
          <li>Provides you with a community to discuss different listings with fellow users.</li>
        </ul>
      </section>

      <section className="mt-5 bg-white border border-slate-200 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-slate-900">Useful Sites Alongside tracker.dev</h2>
        <p className="mt-2 text-slate-700">
          Use these alongside this app to widen your search and discover more roles.
        </p>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          {recommendedSites.map((site) => (
            <a
              key={site.name}
              href={site.url}
              target="_blank"
              rel="noreferrer"
              className="block rounded-xl border border-slate-200 p-4 hover:border-slate-300 hover:bg-slate-50"
            >
              <p className="text-sm font-semibold text-slate-900">{site.name}</p>
              <p className="mt-1 text-xs text-slate-600 leading-relaxed">{site.description}</p>
            </a>
          ))}
        </div>
      </section>
    </div>
  )
}
