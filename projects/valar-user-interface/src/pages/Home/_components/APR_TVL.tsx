import { Separator } from "@/components/ui/separator";
import { APY_DECIMALS } from "@/constants/units";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { algoBigIntToDisplay } from "@/utils/convert";

const APR_TVL = () => {
  const { stakingData } = useAppGlobalState();

  return (
    <div className="flex">
      <div>
        <h1 className="text-lg lg:text-3xl font-bold">{stakingData ? (stakingData.apy.toFixed(APY_DECIMALS) + "%") : "N/A"}</h1>
        <p className="text-sm lg:text-xl font-semibold">APY</p>
      </div>
      <Separator className="mx-6" orientation={"vertical"} />
      <div>
        <h1 className="text-lg lg:text-3xl font-bold">{stakingData ? (Number(algoBigIntToDisplay(stakingData.stakeOnline,"floor", false))/10**9).toFixed(3) + "B ALGO" : "N/A"}</h1>
        <p className="text-sm lg:text-xl font-semibold">Total Network Stake</p>
      </div>
    </div>
  );
};

export default APR_TVL;
