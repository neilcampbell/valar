import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

import APR_TVL from "./APR_TVL";
import { useWallet } from "@txnlab/use-wallet-react";
import { Wallet } from "@/components/Wallet/Wallet";

const HeroSection = () => {
  const navigate = useNavigate();
  const {activeWallet} = useWallet();

  return (
    <div className="flex flex-col gap-2 py-5 lg:gap-6 lg:py-16">
      <h1 className="text-4xl font-extrabold lg:text-6xl">
        Peer-to-Peer <br /> Staking Platform
      </h1>
      <p className="text-sm font-semibold lg:text-xl">
        Valar is a decentralized platform for simple <br /> 
        peer-to-peer staking on the Algorand blockchain.
      </p>
      <APR_TVL />
      {!activeWallet ? (
        <Wallet className="mt-8 w-full lg:w-fit min-w-72" onClick={() => {navigate("stake")}} variant={"v_outline"} text={"Connect Wallet & Start Staking"}/>
      ) : (
        <Button className="mt-8 w-full lg:w-fit min-w-72" variant={"v_outline"} onClick={() => navigate("stake")}>
          Start Staking
        </Button>
      )}
    </div>
  );
};

export default HeroSection;
