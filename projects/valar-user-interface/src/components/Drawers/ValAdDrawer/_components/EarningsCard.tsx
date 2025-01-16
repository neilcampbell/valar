import { adIncome } from "@/api/contract/ValidatorAdCalls";
import { fetchValEarnings } from "@/api/queries/validator-ads";
import {
  InfoItem,
  InfoLabel,
  InfoValue,
} from "@/components/Info/InfoUtilsCompo";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { Earning } from "@/lib/types";
import useUserStore from "@/store/userStore";
import { CURRENCIES } from "@/constants/platform";
import { useWallet } from "@txnlab/use-wallet-react";
import { useState, useEffect } from "react";
import { assetAmountToFeeDisplay } from "@/utils/convert";
import { AssetParams } from "@/constants/units";
import { notify } from "@/components/Notification/notification";



const EarningsCard = ({
  gsValAd,
}: {
  gsValAd: ValidatorAdGlobalState,
}) => {

  const [earnings, setEarnings] = useState<Earning[]>([]);
  const [gettingIncome, setGettingIncome] = useState<boolean>(false);
  const [selectedCurrency, setSelectedCurrency] = useState<string | undefined>(undefined);
  const { activeAddress, transactionSigner } = useWallet();
  const { user } = useUserStore();
  const { algorandClient, noticeboardApp } = useAppGlobalState();
  const algodClient = algorandClient.client.algod;

  // Fetching all earnings at Validator Ad
  useEffect(() => {
    const fetch = async () => {
      if(!gettingIncome){
        console.log("Fetching currencies and earnings of ad.");
        try {
          const earnings = await fetchValEarnings(algodClient, gsValAd);
          setEarnings(earnings);
          setSelectedCurrency(gsValAd.termsPrice.feeAssetId.toString()); // By default, display earnings of current asset
        } catch {
          setEarnings([]);
        }
      }
    };

    fetch();
  }, [gsValAd, gettingIncome]);

  const selectedEarningData = earnings.find((earning) => earning.id.toString() === selectedCurrency);

  const handleIncome = async () => {
    console.log("Withdrawing earnings...");
    setGettingIncome(true);
    const assetId = gsValAd.termsPrice.feeAssetId;

    try{
      const res = await adIncome({
        noticeBoardClient: noticeboardApp.client,
        userAddress: activeAddress!,
        userInfo: user?.userInfo!,
        valAppId: gsValAd.appId,
        valAssetId: assetId,
        signer: transactionSigner,
      });

      if(res.confirmation){
        console.log(`Withdrew earnings for asset ID ${assetId} in amount ${res.return}.`);
        console.log(res.transactions[0].txID());
        notify({ title: "Withdrew successfully", variant: "success" });
      }
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Withdraw failed", variant: "error" });
    }

    setGettingIncome(false);
  }

  return (
    <div className="rounded-lg border border-border bg-background-light p-3">
      <div className="flex items-center gap-1 text-sm">
        <div>Your earnings for</div>
        <Select
          value={selectedCurrency}
          onValueChange={(value) => setSelectedCurrency(value)}
        >
          <SelectTrigger className="w-auto border-0 p-0 focus:ring-0 active:ring-0">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {earnings.map((item, index) => (
              <SelectItem key={index} value={item.id.toString()}>
                {CURRENCIES.get(item.id)!.ticker || "Unknown"}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="my-2 space-y-2">
        <InfoItem className="flex gap-1">
          <InfoLabel>Total earnings:</InfoLabel>
          <InfoValue>{selectedEarningData ? assetAmountToFeeDisplay(selectedEarningData.total, selectedEarningData.id, AssetParams.total, true) : "N/A"}</InfoValue>
        </InfoItem>
        <InfoLabel className="flex gap-1">
          <InfoLabel>Unclaimed earnings:</InfoLabel>
          <InfoValue>{selectedEarningData ? assetAmountToFeeDisplay(selectedEarningData.unclaimed, selectedEarningData.id, AssetParams.total, true) : "N/A"}</InfoValue>
        </InfoLabel>
      </div>
      <Button className="w-full" variant={"v_primary"} onClick={handleIncome}>
        Get Earnings
      </Button>
    </div>
  );
};

export default EarningsCard;
