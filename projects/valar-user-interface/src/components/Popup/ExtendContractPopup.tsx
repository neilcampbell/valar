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

const ExtendContractPopup = ({ isOpen, setOpen, handleExtend }: {isOpen: boolean, setOpen: Dispatch<SetStateAction<boolean>>, handleExtend: () => void}) => {
  return (
    <AlertDialog open={isOpen} onOpenChange={setOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-text text-base font-semibold">
            Define your new staking requirements.
          </AlertDialogTitle>
          <AlertDialogDescription className="text-text-tertiary text-sm">
            To extend the staking with the same node runner, please define your new requirements.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div>
          Coming soon.
        </div>
        <AlertDialogFooter className="w-full">
          <AlertDialogCancel className="flex-grow">Cancel</AlertDialogCancel>
          <AlertDialogAction className="flex-grow" onClick={handleExtend}>
            Extend
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default ExtendContractPopup;
