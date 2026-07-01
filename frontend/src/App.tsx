import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import SeriesPage from './pages/SeriesPage'
import AddSeriesPage from './pages/AddSeriesPage'
import LogPage from './pages/LogPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<SeriesPage />} />
          <Route path="/series" element={<SeriesPage />} />
          <Route path="/add_series" element={<AddSeriesPage />} />
          <Route path="/log" element={<LogPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
