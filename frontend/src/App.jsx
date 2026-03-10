import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Opportunities from './pages/Opportunities'
import Tracker from './pages/Tracker'
import About from './pages/About'

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <p>404 - Page not found</p>
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/opportunities" element={<Opportunities />} />
        <Route path="/tracker" element={<Tracker />} />
        <Route path="/about" element={<About />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}

export default App
