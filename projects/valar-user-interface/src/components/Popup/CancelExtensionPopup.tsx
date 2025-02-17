import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import useUserStore from "@/store/userStore";
import { useEffect } from "react";

const CancelExtensionPopup = ({
  setRenewDelCo,
}: {
  setRenewDelCo: React.Dispatch<React.SetStateAction<DelegatorContractGlobalState | undefined>>;
}) => {
  const { user } = useUserStore();
  const gsDelCoCurrent = user?.userApps && Array.from((user.userApps as Map<bigint, DelegatorContractGlobalState>).values()).find(
    (gsDelCo) => gsDelCo.delBeneficiary === user.beneficiary.address,
  );

  /**
   * =====================================
   *   Disable Renewing-Mode on unmount
   * =====================================
   */

  useEffect(() => {
    return () => setRenewDelCo(undefined);
  }, []);

  return (
    <div className="flex pr-1">
      <Dialog>
        <DialogTrigger asChild>
          <Button variant={"v_outline"} size={"sm"} className="h-6 w-fit pl-1 pr-1 text-xs font-normal">
            Renewing
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-base font-semibold text-text">Renewing contract</DialogTitle>
            <DialogDescription className="text-sm text-text-tertiary">
              To renew your contract with ID {gsDelCoCurrent!.appId.toString()} please select your new staking
              requirement and a node runner. On renewal, your current contract will be cancelled and a new one created,
              possibly with new terms. Do you want to cancel the contract renewal?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="w-full">
            <DialogClose className="flex-grow" asChild>
              <Button variant={"v_primary"}>No</Button>
            </DialogClose>
            <DialogClose className="flex-grow" asChild>
              <Button
                variant={"v_outline"}
                onClick={() => {
                  setRenewDelCo(undefined);
                }}
              >
                Yes
              </Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CancelExtensionPopup;
