import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LandingPage } from '../features/landing/pages/LandingPage'
import { PlayPlaceholder } from '../pages/PlayPlaceholder'
import { NotFound } from '../pages/NotFound'

export const router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/play" element={<PlayPlaceholder />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}