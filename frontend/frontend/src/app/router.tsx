import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LandingPage } from '../features/landing/pages/LandingPage'
import { AuthPage } from '../features/auth/pages/AuthPage'
import { GoogleCallbackPage } from '../features/auth/pages/GoogleCallbackPage'
import { LobbyPage } from '../pages/LobbyPage'
import { RoomPage } from '../features/room/pages/RoomPage'
import { NotFound } from '../pages/NotFound'

export const router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/lobby" element={<LobbyPage />} />
        <Route path="/room/:code" element={<RoomPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}