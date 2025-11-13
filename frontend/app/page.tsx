import HeroSection from '@/components/landing/hero-section';
import HowItWorksSection from '@/components/landing/how-it-works-section';
import WhyItWorksSection from '@/components/landing/why-it-works-section';
import PricingSection from '@/components/landing/pricing-section';
import FaqSection from '@/components/landing/faq-section';
import TestimonialSection from '@/components/landing/testimonial-section';

export default function Home() {
  return (
    <>
      <HeroSection />
      <HowItWorksSection />
      <WhyItWorksSection />
      <PricingSection />
      <FaqSection />
      <TestimonialSection />
    </>
  );
}
