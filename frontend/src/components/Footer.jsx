import { Link } from 'react-router-dom'
import { FaInstagram, FaLinkedin, FaWhatsapp } from 'react-icons/fa'

const CONTACT_EMAIL = 'tadamien8@gmail.com'
const CONTACT_PHONE = '+44 7984 980229'

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white mt-10">
      <div className="max-w-6xl mx-auto px-6 py-10 grid gap-10 md:grid-cols-4">
        <div className="flex flex-col items-center md:items-start">
          <Link to="/" className="inline-flex items-center text-black">
            <p className="text-5xl leading-none font-medium tracking-tight">tracker.dev</p>
          </Link>

          <div className="flex justify-center md:justify-start gap-4 mt-8 text-3xl text-black">
            <a href="https://instagram.com" target="_blank" rel="noreferrer" className="hover:opacity-70" aria-label="Instagram">
              <FaInstagram />
            </a>
            <a href="https://linkedin.com" target="_blank" rel="noreferrer" className="hover:opacity-70" aria-label="LinkedIn">
              <FaLinkedin />
            </a>
            <a href="https://whatsapp.com" target="_blank" rel="noreferrer" className="hover:opacity-70" aria-label="WhatsApp">
              <FaWhatsapp />
            </a>
          </div>
        </div>

        <div>
          <h3 className="text-2xl font-medium text-black">Services</h3>
          <ul className="mt-4 space-y-2 text-black">
            <li>
              <Link to="/opportunities" className="hover:opacity-70">Find Opportunities</Link>
            </li>
            <li>
              <Link to="/about" className="hover:opacity-70">Career Advice</Link>
            </li>
            <li>
              <Link to="/tracker" className="hover:opacity-70">Tracker</Link>
            </li>
            <li>
              <Link to="/about" className="hover:opacity-70">CV Review</Link>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-2xl font-medium text-black">Quick Links</h3>
          <ul className="mt-4 space-y-2 text-black">
            <li>
              <Link to="/about" className="hover:opacity-70">About Us</Link>
            </li>
            <li>
              <Link to="/tracker" className="hover:opacity-70">Community Hub</Link>
            </li>
            <li>
              <Link to="/about" className="hover:opacity-70">CV Template</Link>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-2xl font-medium text-black">Get In Touch</h3>
          <div className="mt-4 text-black space-y-2">
            <p>Email: <a className="hover:opacity-70" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a></p>
            <p>Phone: <a className="hover:opacity-70" href={`tel:${CONTACT_PHONE.replace(/\s+/g, '')}`}>{CONTACT_PHONE}</a></p>
          </div>
          <p className="mt-6">
            <a href="#" className="text-black hover:opacity-70">Terms and Conditions</a>
          </p>
        </div>
      </div>
    </footer>
  )
}
