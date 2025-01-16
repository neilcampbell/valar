import { Button } from "@/components/ui/button";
import { Buffer } from "buffer";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { UserInfo } from "@/interfaces/contracts/User";
import { cn } from "@/lib/shadcn-utils";
import { KeyRegParams } from "@/lib/types";
import useUserStore from "@/store/userStore";
import { useWallet } from "@txnlab/use-wallet-react";
import { LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { ASA_ID_ALGO } from "@/constants/smart-contracts";
import { ellipseAddress } from "@/utils/convert";

export const Wallet = ({ className, onClick, variant="wallet", text="Connect Wallet" }: { className?: string, onClick?: () => void, variant?: "wallet" | "v_outline", text?: string }) => {
  const {
    activeAddress,
    wallets,
    activeWallet,
    activeAccount,
    activeWalletAccounts,
  } = useWallet();
  const { user, setUser } = useUserStore();
  const { algorandClient } = useAppGlobalState();
  const [open, onOpenChange] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    const fetch = async () => {
      console.log(`Fetching user info for ${activeAddress}.`)
      //Fetching user role and algo amount
      if (activeAddress) {
        try{
          const userInfo = await UserInfo.getUserInfo(algorandClient.client.algod, activeAddress);
          const res = await algorandClient.client.algod.accountInformation(activeAddress).do()
          const algo: bigint = res["amount"];
          const assets = new Map<bigint, bigint>();
          assets.set(ASA_ID_ALGO, algo);
          res["assets"].forEach((asset: { "amount": bigint, "asset-id": bigint, "is-frozen": boolean }) => {
            assets.set(BigInt(asset["asset-id"]), BigInt(asset["amount"]));
          });

          console.log("Assets :: ")
          console.log(assets)

          let keyRegParams = undefined;
          if(res["participation"]){
            keyRegParams = {
              voteKey: new Uint8Array(Buffer.from(res["participation"]["vote-participation-key"], 'base64')),
              selectionKey: new Uint8Array(Buffer.from(res["participation"]["selection-participation-key"], 'base64')),
              voteFirst: BigInt(res["participation"]["vote-first-valid"]),
              voteLast: BigInt(res["participation"]["vote-last-valid"]),
              voteKeyDilution: BigInt(res["participation"]["vote-key-dilution"]),
              stateProofKey: new Uint8Array(Buffer.from(res["participation"]["state-proof-key"], 'base64')),
            } as KeyRegParams;
          }

          console.log("Key reg parameters of user: ", keyRegParams);

          const trackedPerformance = res["incentive-eligible"] as boolean;

          setUser({address: activeAddress, algo: algo, assets: assets, keyRegParams: keyRegParams, trackedPerformance: trackedPerformance, userInfo: userInfo});
        } catch (error) {
          console.error("Error in fetching user:", error);
        }
      } else {
        if(user) {
          // Clear user
          setUser( null );
        }
      }
    };

    fetch();
  }, [activeAddress]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button variant={variant} className={cn("", className)}>
          {ellipseAddress(activeAddress as string) ?? text}
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          {!activeWallet ?
            <DialogTitle> Connect Your Wallet </DialogTitle> :
            <DialogTitle> Modify Your Wallet </DialogTitle>
          }
          <DialogDescription>
            Select your wallet to access your account.
          </DialogDescription>
        </DialogHeader>
        {!activeWallet ? (
          <div className="flex flex-col gap-4">
            {wallets.map((wallet) => (
              <div
                className="flex w-full cursor-pointer items-center gap-4 rounded-lg p-2 hover:bg-background"
                key={wallet.id}
                onClick={async () => {
                  try{
                    const connectedWalletAccount = await wallet.connect();
                    if(connectedWalletAccount.length > 0){
                      onOpenChange(false);
                      if(onClick) onClick();
                    } else {
                      console.log("No wallet account connected.")
                    }
                  } catch {
                    console.log("Wallet was not connected.")
                  }
                }}
              >
                <img
                  src={wallet.metadata.icon}
                  className="h-9 w-9 rounded-lg"
                />
                <div className="w-auto">{wallet.metadata.name}</div>
              </div>
            ))}
          </div>
        ) : (
          <div>
            <div className="flex w-full items-center gap-4 rounded-lg bg-background p-2">
              <img
                src={activeWallet.metadata.icon}
                className="h-9 w-9 rounded-lg"
              />
              <div className="flex w-auto flex-grow items-center justify-between">
                <div className="">
                  <h1>{activeWallet.metadata.name} </h1>
                  <h6 className="max-w-lg text-xs">
                    {ellipseAddress(activeAccount!.address as string)}
                  </h6>
                </div>
                <div>
                  <LogOut
                    className="mr-2 h-5 w-5 cursor-pointer"
                    onClick={() => activeWallet.disconnect()}
                  />
                </div>
              </div>
            </div>
            <Select
              defaultValue={activeAddress as string}
              onValueChange={(value) => activeWallet.setActiveAccount(value)}
            >
              <SelectTrigger className="mt-4 w-[180px] border-opacity-50">
                <SelectValue
                  defaultValue={activeAccount?.name}
                  placeholder="Choose a Address"
                />
              </SelectTrigger>
              <SelectContent>
                {activeWalletAccounts?.map((acc, index) => (
                  <SelectItem key={index} value={acc.address}>
                    {ellipseAddress(acc.address)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
