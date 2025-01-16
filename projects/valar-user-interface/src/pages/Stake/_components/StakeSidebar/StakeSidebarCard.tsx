import InfoCard from "./InfoCard";
import { Separator } from "@/components/ui/separator";
import { algoBigIntToDisplay } from "@/utils/convert";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";


const StakeSidebarCard = () => {
  const { stakingData } = useAppGlobalState();

  if(!stakingData) return;

  return (
    <div className="rounded-lg bg-background-light px-2 py-3">
      <h1 className="text-base font-bold px-2">Algorand Staking Stats</h1>
      <Separator className="mt-2 hidden bg-border lg:block" />
      <div className="p-2">
        <div className="flex flex-col gap-4">
          <InfoCard title="Online stake" value={(Number(algoBigIntToDisplay(stakingData.stakeOnline,"floor", false))/10**9).toFixed(3) + "B ALGO"} />
          <InfoCard title="Mainnet nodes" value={stakingData.nodesTotal.toString()} />
          <InfoCard title="Online accounts" value={stakingData.accountsOnlineAll.toString()} />
          <InfoCard title="Online accounts with +30k ALGO" value={stakingData.accountsOnline30k.toString()} />
        </div>
      </div>
    </div>
  );
};

export default StakeSidebarCard;
