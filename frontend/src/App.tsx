import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import SeriesPage from './pages/SeriesPage'
import AddSeriesPage from './pages/AddSeriesPage'
import ManageSeriesPage from './pages/ManageSeriesPage'
import ConfigPage from './pages/ConfigPage'
import LogPage from './pages/LogPage'

const NAV_LINKS = [
  { to: '/series', label: 'Series' },
  { to: '/add_series', label: 'Add Series' },
  { to: '/manage_series', label: 'Manage Series' },
  { to: '/config', label: 'Config' },
  { to: '/log', label: 'Log' },
]

function App() {
  return (
    <BrowserRouter>
      <nav className="flex gap-2 p-4">
        {NAV_LINKS.map(({ to, label }) => (
          <Button key={to} variant="ghost" asChild>
            <NavLink to={to}>{label}</NavLink>
          </Button>
        ))}
      </nav>
      <Routes>
        <Route path="/" element={<SeriesPage />} />
        <Route path="/series" element={<SeriesPage />} />
        <Route path="/add_series" element={<AddSeriesPage />} />
        <Route path="/manage_series" element={<ManageSeriesPage />} />
        <Route path="/config" element={<ConfigPage />} />
        <Route path="/log" element={<LogPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
