import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import SeriesPage from './pages/SeriesPage'
import AddSeriesPage from './pages/AddSeriesPage'
import ManageSeriesPage from './pages/ManageSeriesPage'
import ConfigPage from './pages/ConfigPage'
import LogPage from './pages/LogPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<SeriesPage />} />
          <Route path="/series" element={<SeriesPage />} />
          <Route path="/add_series" element={<AddSeriesPage />} />
          <Route path="/manage_series" element={<ManageSeriesPage />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/log" element={<LogPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
