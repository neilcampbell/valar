import { Wallet } from "@/components/Wallet/Wallet";
import { cn } from "@/lib/shadcn-utils";

const ConnectWalletCard = ({ className, drawerClose }: { className?: string, drawerClose: () => void }) => {
  return (
    <div
      className={cn(
        "h-min w-auto rounded-lg bg-gradient-to-br from-gradient-light to-gradient-dark p-3",
        className,
      )}
    >
      <h1 className="font-bold">Connect your Wallet</h1>
      <p className="mt-3 text-sm">
        Please connect your wallet to start staking.
      </p>
      <Wallet className="mt-6 w-full" onClick={drawerClose}/>
    </div>
  );
};

export default ConnectWalletCard;
