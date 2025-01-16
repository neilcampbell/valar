import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Dispatch, SetStateAction } from "react";

const WithdrawContractPopup = ({ isOpen, setOpen, handleWithdraw, delAppId}: {isOpen: boolean, setOpen: Dispatch<SetStateAction<boolean>>, handleWithdraw: () => void, delAppId: bigint}) => {
  return (
    <AlertDialog open={isOpen} onOpenChange={setOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-text text-base font-semibold">
            Are you sure want to withdraw from the contract?
          </AlertDialogTitle>
          <AlertDialogDescription className="text-text-tertiary text-sm">
            You are withdrawing from contract with ID: {delAppId.toString()}.
            <br/>
            You will stop staking.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="w-full">
          <AlertDialogCancel className="flex-grow">Cancel</AlertDialogCancel>
          <AlertDialogAction className="flex-grow bg-error hover:bg-error" onClick={handleWithdraw}>
            Withdraw
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default WithdrawContractPopup;
