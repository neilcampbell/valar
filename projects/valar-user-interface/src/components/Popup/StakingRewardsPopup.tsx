import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const StakingRewardsDialog = () => {
  return (
    <Dialog>
      <DialogTrigger>Open</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Notice about Staking Rewards</DialogTitle>
        </DialogHeader>
        <div className="text-text-tertiary">
          <div className="text-sm">
            Your balance is below 30,000 ALGO - the minimum defined by the
            Algorand network to be eligible for staking rewards. You will be
            able to earn Algorand staking rewards with peer-to-peer staking only
            if you increase your balance above the minimum. You acknowledge this
            by continuing to use the platform.
          </div>
          <div className="mt-6 text-sm">
            You can earn staking rewards with your current balance using Valar's
            Reti staking pool.
          </div>
          <div className="mt-4 flex gap-2">
            <DialogClose>
              <Button variant={"v_outline"}>Cancel</Button>
            </DialogClose>
            <Button variant={"v_primary"} className="flex-grow">
              Continue
            </Button>
            <Button variant={"v_tertiary"} className="flex-grow">
              To Staking
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default StakingRewardsDialog;
