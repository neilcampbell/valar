import { UserQuery } from "@/api/queries/user";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useDelCoDrawer } from "@/contexts/DelCoDrawerContext";
import useUserStore from "@/store/userStore";
import { useNavigate } from "react-router-dom";

const RenewContractButton = ({ valAppId }: { valAppId: bigint }) => {
  const { gsDelCo } = useDelCoDrawer();
  const { setRenewDelCo, valAdsMap, algorandClient } = useAppGlobalState();
  const { user, setUser } = useUserStore();
  const navigate = useNavigate();

  const handleRenew = async () => {
    if (!user || !gsDelCo) return;

    // Mark that user wants to renew the contract
    setRenewDelCo(gsDelCo);

    // Set the correct beneficiary if it is not already
    let beneficiary = user.beneficiary;
    const delBeneficiary = gsDelCo!.delBeneficiary;
    if ( beneficiary.address !== delBeneficiary ) {
      beneficiary = await UserQuery.getAccountInfo(algorandClient.client.algod, delBeneficiary);
    }
    setUser({ ...user, beneficiary });

    // Get current validator owner
    const gsValAd = valAdsMap?.get(valAppId);
    navigate("/stake" + "?node_runner=" + gsValAd?.valOwner);
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant={"v_primary"} className="w-1/2 text-sm">
          Renew Contract
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-base font-semibold text-text">
            Renew your contract at Stake page
          </AlertDialogTitle>
          <AlertDialogDescription className="text-sm text-text-tertiary">
            Contract renewal consists of simultaneously withdrawing from the current contract and starting a new one.
            The new contract can be with the same or a different node runner, possibly with new terms.
            To renew the contract, please continue on Stake page, define your new staking requirement, and select your desired node runner.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="w-full">
          <AlertDialogCancel className="w-1/2">Cancel</AlertDialogCancel>
          <AlertDialogAction className="w-1/2" onClick={handleRenew}>
            Go to Stake page
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default RenewContractButton;
