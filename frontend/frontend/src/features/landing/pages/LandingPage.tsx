import { Navbar } from '@/components/layout/Navbar'
import { Footer } from '@/components/layout/Footer'
import { HeroSection } from '@/features/landing/components/HeroSection'
import { GamePreview } from '@/features/landing/components/GamePreview'
import { HowItWorks } from '@/features/landing/components/HowItWorks'
import { RolesSection } from '@/features/landing/components/RolesSection'
import { RoundExample } from '@/features/landing/components/RoundExample'
import { AIAnalysisTeaser } from '@/features/landing/components/AIAnalysisTeaser'
import { FinalCTA } from '@/features/landing/components/FinalCTA'

export const LandingPage = () => {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <GamePreview />
        <HowItWorks />
        <RolesSection />
        <RoundExample />
        <AIAnalysisTeaser />
        <FinalCTA />
      </main>
      <Footer />
    </>
  )
}