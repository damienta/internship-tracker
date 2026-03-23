import locationIcon from '../assets/location.png'

const SOURCE_LABELS = {
  lever: 'Lever',
  greenhouse: 'Greenhouse',
  ashby: 'Ashby',
  bt: 'BT',
  hsbc: 'HSBC',
  sap: 'SAP',
}

function formatDate(value) {
  if (!value) return null
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function JobCard({
  job,
  showApply = true,
  showDateChips = true,
  showSkills = true,
  compact = false,
}) {
  return (
    <div className={`bg-white border border-gray-200 rounded-xl flex flex-col ${compact ? 'p-3 gap-1.5' : 'p-5 gap-2'}`}>
      <div className={`flex items-start justify-between ${compact ? 'gap-3' : 'gap-4'}`}>
        <div>
          <h2 className={`font-semibold text-gray-900 leading-snug ${compact ? 'text-sm' : 'text-base'}`}>{job.title}</h2>
          <p className={`text-gray-500 ${compact ? 'text-xs' : 'text-sm'}`}>{job.company}</p>
        </div>

        {showApply && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`shrink-0 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors ${compact ? 'text-xs px-3 py-1' : 'text-sm px-4 py-1.5'}`}
          >
            Apply
          </a>
        )}
      </div>

      <div className={`flex flex-wrap text-gray-500 ${compact ? 'gap-1.5 text-[11px]' : 'gap-2 text-xs'}`}>
        {job.location && (
          <span className="inline-flex items-center gap-1">
            <img src={locationIcon} alt="" className="w-4 h-4 opacity-70" />
            {job.location}
          </span>
        )}

        {job.source_website && (
          <span className="bg-gray-100 px-2 py-0.5 rounded">
            {SOURCE_LABELS[job.source_website] ?? job.source_website}
          </span>
        )}

        {showDateChips && formatDate(job.date_posted) && (
          <span className="bg-green-50 text-green-700 px-2 py-0.5 rounded">
            Opened {formatDate(job.date_posted)}
          </span>
        )}

        {showDateChips && formatDate(job.deadline) && (
          <span className="bg-amber-50 text-amber-700 px-2 py-0.5 rounded">
            Deadline {formatDate(job.deadline)}
          </span>
        )}
      </div>

      {showSkills && job.extracted_skills?.length > 0 && (
        <div className={`flex flex-wrap ${compact ? 'gap-1' : 'gap-1 mt-1'}`}>
          {job.extracted_skills.slice(0, compact ? 4 : 6).map((skill) => (
            <span key={skill} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
              {skill}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
