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

function getDaysLeftLabel(daysLeft) {
  if (daysLeft === null) return 'No deadline'
  if (daysLeft < 0) return 'Expired'
  if (daysLeft === 0) return 'Due today'
  if (daysLeft === 1) return '1 day left'
  return `${daysLeft} days left`
}

export default function DeadlineJobCard({ job, daysLeft }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h4 className="text-sm font-semibold text-gray-900 leading-snug line-clamp-2">{job.title}</h4>
          <p className="text-xs text-gray-600 truncate">{job.company}</p>
        </div>

        <span className="shrink-0 text-[11px] font-medium bg-amber-50 text-amber-700 px-2 py-1 rounded-full">
          {getDaysLeftLabel(daysLeft)}
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5 text-[11px] text-gray-500">
        {job.location && (
          <span className="inline-flex items-center gap-1">
            <img src={locationIcon} alt="" className="w-3.5 h-3.5 opacity-70" />
            {job.location}
          </span>
        )}

        {job.source_website && (
          <span className="bg-gray-100 px-2 py-0.5 rounded">
            {SOURCE_LABELS[job.source_website] ?? job.source_website}
          </span>
        )}

        {formatDate(job.deadline) && (
          <span className="bg-amber-50 text-amber-700 px-2 py-0.5 rounded">
            Deadline {formatDate(job.deadline)}
          </span>
        )}
      </div>

      <a
        href={job.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-center bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 transition-colors"
      >
        Apply
      </a>
    </div>
  )
}