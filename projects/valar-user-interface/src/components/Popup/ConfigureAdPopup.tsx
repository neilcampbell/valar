import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Dispatch, SetStateAction } from "react";

const ConfigureAdPopup = ({ isOpen, setOpen, handleConfigure}: {isOpen: boolean, setOpen: Dispatch<SetStateAction<boolean>>, handleConfigure: () => void}) => {
  return (
    <AlertDialog open={isOpen} onOpenChange={setOpen}>
      <AlertDialogContent className="w-[390px]">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-text text-base font-semibold">
            Your Ad is being prepared.
          </AlertDialogTitle>
          <AlertDialogDescription className="text-text-tertiary text-sm">
            Your ad is almost ready. Please complete the configuration and it will get automatically published!
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="w-full">
          <AlertDialogAction className="flex-grow" onClick={handleConfigure}>
            Configure
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default ConfigureAdPopup;
