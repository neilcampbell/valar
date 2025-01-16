import { Wallet } from "./Wallet";

const ConnectWalletDisclaimer = () => {
  return (
    <div className="flex flex-col items-center justify-between pt-40">
      <h1 className="font-semibold">Connect your Wallet</h1>
      <div className="flex flex-col items-center">
        <p className="mt-2 text-sm text-text-tertiary">
          Please connect your wallet to see your dashboard
        </p>
        <Wallet className="mt-10 w-full" />
      </div>
    </div>
  );
};

export default ConnectWalletDisclaimer;
