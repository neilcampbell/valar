import { Container } from "@/components/Container/Container";

import StakeListCard from "./_components/StakeList/StakeListCard";
import StakePotentialCard from "./_components/StakePotential/StakePotentialCard";
import StakeRequirementCard from "./_components/StakeRequirement/StakeRequirementCard";
import StakeSidebarCard from "./_components/StakeSidebar/StakeSidebarCard";
import { StakeReqs } from "@/lib/types";
import { useState } from "react";
import { DEFAULT_MAX_STAKE, PAYMENT_ASA, SUGGESTED_DURATION } from "@/constants/platform";
import { durationToRounds } from "@/utils/convert";
import { TimeParams } from "@/constants/units";

const StakePage: React.FC = () => {
  const [stakeReqs, setStakeReqs] = useState<StakeReqs>({duration: durationToRounds(SUGGESTED_DURATION, TimeParams.stake.unit), maxStake: DEFAULT_MAX_STAKE, currency: PAYMENT_ASA});

  return (
    <Container>
      <div className="grid gap-2 lg:grid-cols-12">
        <div className="col-span-9 flex flex-col gap-2">
          <div className="flex gap-2 flex-wrap  lg:flex-nowrap">
            <StakeRequirementCard setStakeReqs={setStakeReqs} className="w-full" />
            <StakePotentialCard stakeReqs={stakeReqs} className="lg:flex-1 lg:min-w-[260px]" />
          </div>
          <StakeListCard stakeReqs={stakeReqs} />
        </div>
        <div className="col-span-3 hidden lg:block">
          <StakeSidebarCard />
        </div>
      </div>
    </Container>
  );
};

export default StakePage;
