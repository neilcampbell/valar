import { Container } from "@/components/Container/Container";

import HeroSection from "./_components/HeroSection";
import NodeRunnerSection from "./_components/NodeRunnerSection";
import PartnersSection from "./_components/PartnersSection";
import StakingSection from "./_components/StakingSection";

const HomePage = () => {
  return (
    <Container>
      <HeroSection />
      <div className="mt-5 flex flex-col gap-14 lg:gap-32 lg:py-16">
        <StakingSection />
        <NodeRunnerSection />
      </div>
      <PartnersSection />
    </Container>
  );
};

export default HomePage;
