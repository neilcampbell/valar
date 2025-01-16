import ITooltip from "@/components/Tooltip/ITooltip";
import { Separator } from "@/components/ui/separator";
import { Wallet } from "@/components/Wallet/Wallet";
import { cn } from "@/lib/shadcn-utils";
import { ToolTips } from "@/constants/tooltips";
import useUserStore from "@/store/userStore";
import { algoBigIntToDisplay, estimateRateForRounds } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { APY_DECIMALS } from "@/constants/units";
import { useEffect, useState } from "react";
import { ParamsCache } from "@/utils/paramsCache";
import { StakeReqs } from "@/lib/types";

const StakePotentialCard =
({
  stakeReqs,
  className,
}: {
  stakeReqs: StakeReqs;
  className?: string;
}) => {
  const { stakingData } = useAppGlobalState();
  const { activeAccount } = useWallet();
  const { user } = useUserStore();

  const [possibleReward, setPossibleReward] = useState<bigint | undefined>(undefined);

  // Get possible reward estimation
  useEffect(() => {
    const fetch = async () => {
      try {
        if(user && stakeReqs && stakingData){
          const currentRound = await ParamsCache.getRound();
          const returnRate = estimateRateForRounds(currentRound, stakingData.stakeOnline, stakeReqs.duration) /100;
          const possibleReward = BigInt( Math.floor( Number(user.algo) * returnRate));
          setPossibleReward(possibleReward);
        }
      } catch (error) {
        console.error('Error fetching estimating possilbe reward:', error);
      }
    }

    fetch();
  }, [stakingData, user, stakeReqs]);

  
  return (
    <div
      className={cn(
        "w-full rounded-lg bg-transparent lg:bg-background-light lg:px-2 lg:py-3",
        className,
      )}
    >
      <h1 className="text-base font-bold px-2"> Your Staking Potential </h1>
      <Separator className="mt-2 hidden bg-border lg:block" />
      <div className="p-2">
        <div className="space-y-2 rounded-lg bg-background-light p-2 lg:bg-transparent lg:p-0">
          {activeAccount && user ? (
            <>
              <div className="flex flex-wrap gap-1 text-sm">
                <div className="text-text-tertiary">
                  Algorand rewards <ITooltip value={ToolTips.AlgorandRewards}/>{" "}:
                </div>
                <div> {stakingData ? (stakingData.apy.toFixed(APY_DECIMALS) + "%") : "N/A"} </div>
              </div>
              <div className="flex flex-wrap gap-1 text-sm">
                <div className="text-text-tertiary"> Your stake: </div>
                <div> {algoBigIntToDisplay(user.algo, "floor", true)} </div>
              </div>
              <div className="flex flex-wrap gap-1 text-sm">
                <div className="text-text-tertiary">
                  Possible reward <ITooltip value={ToolTips.PossibleRewards}/>{" "}:
                </div>
                <div> {possibleReward ? algoBigIntToDisplay(possibleReward, "floor", true) : "N/A"} </div>
              </div>
            </>
          ) : (
            <>
              <div className="mt-2 flex flex-col items-center gap-3">
                <div className="text-xs text-text-secondary">
                  Connect your wallet to see your potential.
                </div>
                <Wallet />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default StakePotentialCard;
