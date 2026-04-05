export default function Contact() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold text-slate-900">Contact Me</h1>
      <p className="mt-2 text-sm text-slate-600">
        Questions, website feedback, and collaboration ideas are always welcome.
      </p>
      <p className="mt-1 text-sm text-slate-600 leading-relaxed">
        You can also send your CV for advice and feedback. Use the form below or email me directly at <span className="font-medium">tadamien8@gmail.com</span>.
      </p>

      <form
        className="mt-6 bg-white border border-slate-200 rounded-xl p-6 space-y-4"
        action="mailto:tadamien8@gmail.com"
        method="post"
        encType="text/plain"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="name" className="block text-sm text-slate-700 mb-1">Name</label>
            <input
              id="name"
              name="name"
              type="text"
              required
              placeholder="How should we address you?"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm text-slate-700 mb-1">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              required
              placeholder="Where should we send our reply?"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
            />
          </div>
        </div>

        <div>
          <label htmlFor="subject" className="block text-sm text-slate-700 mb-1">Subject</label>
          <input
            id="subject"
            name="subject"
            type="text"
            required
            placeholder="e.g CV feedback request"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
          />
        </div>

        <div>
          <label htmlFor="message" className="block text-sm text-slate-700 mb-1">Message</label>
          <textarea
            id="message"
            name="message"
            rows={5}
            required
            placeholder="Write your message"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
          />
        </div>

        <button
          type="submit"
          className="rounded-lg bg-black text-white px-4 py-2 text-sm hover:opacity-90"
        >
          Send Message
        </button>
      </form>
    </div>
  )
}
