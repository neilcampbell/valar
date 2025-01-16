import { Button } from "@/components/ui/button";
import {
  DollarSign,
  Eye,
  Globe,
  LockOpen,
  Shield,
  ThumbsUp,
} from "lucide-react";

import FeaturesCard from "./FeaturesCard";
import { useNavigate } from "react-router-dom";

const StakingSection = () => {
  const stakingFeatures: { icon: JSX.Element; head: string | JSX.Element; desc: string | JSX.Element }[] = [
    {
      icon: <Shield className="h-8 w-8 text-secondary" />,
      head: "Secure",
      desc: "Your ALGO stay in your wallet and liquid. You never give away their custody.",
    },
    {
      icon: <DollarSign className="h-8 w-8 text-secondary" />,
      head: "Get 100% of Rewards",
      desc: <span>There is <span className="underline">no commission</span> taken from your staking rewards with peer-to-peer staking.</span>
    },
    {
      icon: <Globe className="h-8 w-8 text-secondary" />,
      head: "Decentralized",
      desc: "Stake directly with any node runner around the globe, private or institutional.",
    },
    {
      icon: <Eye className="h-8 w-8 text-secondary" />,
      head: "Transparent",
      desc: "Fix staking costs in advance. Pay in stablecoins or ALGO.",
    },
    {
      icon: <ThumbsUp className="h-8 w-8 text-secondary" />,
      head: "Service Protection",
      desc: "Automatic withdrawal from under-performing services.",
    },
    {
      icon: <LockOpen className="h-8 w-8 text-secondary" />,
      head: "No Locking",
      desc: "ALGO remains unlocked and free to use. Change your staking contract at any time.",
    },
  ];

  const navigate = useNavigate()

  return (
    <div className="grid grid-cols-1 gap-y-6 lg:grid-cols-3 lg:gap-12">
      <div className="col-span-1">
        <div className="flex flex-col gap-1 lg:gap-3">
          <h3 className="text-xs font-semibold text-secondary-dark lg:text-sm">
            ALGORAND USER
          </h3>
          <h1 className="text-xl font-semibold lg:text-3xl">
            Do you have ALGO?
          </h1>
          <p className="text-sm leading-5 lg:text-base lg:leading-7">
            You can stake it to earn staking rewards, protect your assets, and
            decentralize the network.
          </p>
        </div>
        <Button className="mt-6 w-full" variant={"v_secondary"} onClick={() => navigate("stake")}>
          Start Staking
        </Button>
      </div>
      <div className="col-span-2">
        <div className="grid grid-cols-2 gap-x-6 gap-y-12 lg:grid-cols-3">
          {stakingFeatures.map((f, index) => (
            <FeaturesCard key={index} {...f} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default StakingSection;
