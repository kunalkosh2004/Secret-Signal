import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LandingPage } from '../features/landing/pages/LandingPage'
import { AuthPage } from '../features/auth/pages/AuthPage'
import { LobbyPlaceholder } from '../pages/LobbyPlaceholder'
import { NotFound } from '../pages/NotFound'

export const router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/lobby" element={<LobbyPlaceholder />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}