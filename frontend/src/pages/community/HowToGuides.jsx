import { Link } from 'react-router-dom'

export default function HowToGuides() {
  const sections = [
    {
      title: 'How to Prepare for Applications',
      subtitle: 'Build a simple process before you start applying.',
      points: [
        'Create one strong base CV, then tailor it to each role. Do research on what you will do in the role and the companies values.',
        'Apply for roles that match your skillset, would a recruiter hire you if you have none of the skills in the job description?',
        'Read the job description very carefully, make sure to keep a copy of the description as it goes away when interviewing starts.',
        'Have a Cover Letter that highlights your strengths and have a section to talk about why you want to work at X company.',
        'In your CV have proof of impact for your projects (metrics, users, performance), for example it improved processes by X%.',
        'Apply to companies that you are interested in, see if their work interests you and if you share their values.',
        'Applications are a numbers game, the more interviews you get invited to the more experience you will build.',
        'Don\'t be discouraged by rejections, they are a part of the process. You just need one "yes" to get the job, so keep applying and improving with each application.',
      ],
    },
    {
      title: 'How to Prepare for Interviews',
      subtitle: 'Practice the patterns employers repeatedly test.',
      points: [
        'Prepare a 60-second introduction about who you are and what you are looking for.',
        'Have 3-5 stories that you can adapt to common behavioural questions (e.g Tell me about a time you overcame a challenge).',
        'Use the STAR structure (Situation, Task, Action, Result) for behavioural answers.',
        'Understand your CV and be ready to explain every line with confidence.',
        'For technical interviews, ensure you do enough practice (a LeetCode question everyday).',
        'For any interview, ensure the structure is clear, know what you\'re getting yourself into - ask the recruiter for an agenda/format',
        'Research the company: product, values, recent news, why you are a good fit and role-specific expectations from job description.',
        'An interview is two ways, it\'s as much about you finding the right company as it is the company finding the right person.',
        'After interviews, send a follow-up email to thank the interviewers and reiterate your interest in the role.',
        'Prepare questions to ask during or at the end of the interview to show interest and to see if the company is the right fit for you.',
      ],
    },
    {
      title: 'How to Write a CV',
      subtitle: 'Keep it results-focused and easy to scan.',
      points: [
        'CV should be structured in the order of: education, skills, experience, projects and soft skills all in a clear one-page layout.',
        'Use bullet points that start with action verbs (built, led, improved, reduced, delivered).',
        'Quantify outcomes when possible (faster by 30%, supported 500+ users, etc.).',
        'Tailor the CV to the company, prioritise relevant projects with the skills they\'re looking for and remove older, weaker content.',
        'Tailor keywords to match the job description (e.g Java, CI/CD, Python) so your CV passes initial screening.',
      ],
    },
    {
      title: 'How to Write a Cover Letter',
      subtitle: 'Show motivation, fit, and evidence without repeating your CV.',
      points: [
        'Open with why this role and this company specifically matters to you and how you can contribute to the role.',
        'Explain how your background and skills make you a strong candidate for the position.',
        'Show you understand the company\'s mission and values and connect them to your own motivations and experience.',
        'Talk about the soft skills you have that are relevant to the role.',
        'Keep your Cover Letter concise and don\'t repeat your CV, roughly about 3 short paragraphs.',
        'Finish with a confident closing and a clear expression of interest.',
      ],
    },
    {
      title: 'Extra Tips',
      subtitle: 'Small improvements that make a big difference.',
      points: [
        'Apply early when possible, because many (if not all) internship roles are reviewed on a rolling basis.',
        'After interviews, reflect on what went well and what could be improved - keep a list and read before interviews.',
        'Use the resources on this website to follow up and reflect on what is working.',
        'Ask a friend or mentor to harshly review your CV and cover letter before deadlines and applications.',
        'Stay consistent: a steady application rhythm beats last-minute application bursts.',
        'Use different websites to your advantage e.g Glassdoor for company research. Check the Useful Sites section in the About page.',
        'Work hard, if you put in the hard work and effort then you will get the results you want.'
      ],
    },
  ]

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <Link
        to="/community"
        className="inline-flex items-center pr-3 py-3 text-base font-medium text-blue-700 transition-colors hover:text-blue-900 hover:underline"
      >
        {'< Back to Community'}
      </Link>

      <h1 className="text-3xl font-bold text-slate-900">How-To Guides</h1>
      <p className="mt-2 text-slate-600">
        Practical guidance for each stage of internship applications, from CV and cover letter writing to interview prep.
      </p>

      <div className="mt-8 space-y-5">
        {sections.map((section) => (
          <section key={section.title} className="bg-white border border-slate-200 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-slate-900">{section.title}</h2>
            <p className="mt-1 text-slate-600">{section.subtitle}</p>
            <ul className="mt-4 list-disc list-inside space-y-2 text-slate-700">
              {section.points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  )
}
