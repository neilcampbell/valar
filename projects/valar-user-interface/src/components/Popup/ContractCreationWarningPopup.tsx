import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { ContractWarning, ContractWarningConfig } from "@/lib/contract-warnings";
import { cn } from "@/lib/shadcn-utils";

const ContractCreationWarningPopup = ({
  onSubmit,
  openWarning,
  setOpenWarning,
  warnings,
}: {
  onSubmit: () => Promise<void>;
  openWarning: boolean;
  setOpenWarning: React.Dispatch<React.SetStateAction<boolean>>;
  warnings: ContractWarning[];
}) => {
  if (warnings.length === 0) return;

  return (
    <Dialog open={openWarning} onOpenChange={setOpenWarning}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="text-lg font-semibold">Warning!</DialogTitle>
          <DialogDescription className="hidden" />
          <div>
            {warnings.map((warning, index) => {
              const { title, getMessage } = ContractWarningConfig[warning.type];
              return (
                <div key={index}>
                  <Separator className={cn("my-3 bg-border", index === 0 && "mt-0")} />
                  <h1 className="text-sm">{title}:</h1>
                  <div className="text-sm text-text-tertiary">{getMessage(warning.param)}</div>
                </div>
              );
            })}
            <Separator className="my-3 bg-border" />
            <h3 className="text-sm">Are you sure you want to continue?</h3>
          </div>
        </DialogHeader>
        <DialogFooter className="w-full">
          <DialogClose className="flex-grow" asChild>
            <Button variant={"v_outline"}>Cancel</Button>
          </DialogClose>
          <DialogClose className="flex-grow" asChild>
            <Button className="flex-grow bg-error text-lg font-semibold hover:bg-error" onClick={onSubmit}>
              Yes
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ContractCreationWarningPopup;
