import { contractCreate, userCreateAndContractCreate } from "@/api/contract/DelegatorCalls";
import {
  InfoItem,
  InfoLabel,
  InfoValue,
} from "@/components/Info/InfoUtilsCompo";
import ITooltip from "@/components/Tooltip/ITooltip";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { MBR_USER_BOX, MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE } from "@/constants/smart-contracts";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { UserInfo } from "@/interfaces/contracts/User";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { cn } from "@/lib/shadcn-utils";
import { ToolTips } from "@/constants/tooltips";
import { StakeReqs } from "@/lib/types";
import useUserStore from "@/store/userStore";
import { CURRENCIES } from "@/constants/platform";
import { adjustedMaxStakeForGratis, calculateGivenMaxStake, calculateNodeRunnerFee } from "@/utils/contract/helpers";
import { algoBigIntToDisplay, assetAmountToFeeDisplay, ellipseAddress, estimateRateForRounds, roundsToDuration } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { useEffect, useState } from "react";
import TermsAndConditions from "@/components/TermsAndConditions/TermsAndConditions";
import { TC_LATEST } from "@/constants/terms-and-conditions";
import { ALGORAND_DEPOSIT_DECIMALS, APY_DECIMALS, AssetParams, TimeParams } from "@/constants/units";
import { ParamsCache } from "@/utils/paramsCache";
import { notify } from "@/components/Notification/notification";

const ContractCreateCard: React.FC<{
  stakeReqs: StakeReqs,
  gsValAd: ValidatorAdGlobalState,
  setDelAppId: React.Dispatch<React.SetStateAction<bigint | undefined>>,
  setRefetch: React.Dispatch<React.SetStateAction<boolean>>;
  partnerAddress?: string,
  className?: string
}> = ({
  stakeReqs,
  gsValAd,
  setDelAppId,
  setRefetch,
  partnerAddress,
  className
}) => {

  const { activeAddress, transactionSigner } = useWallet();
  const { user, setUser } = useUserStore();
  const { algorandClient, noticeboardApp, stakingData } = useAppGlobalState();

  const [role, setRole] = useState<string>("");
  const [termsChecked, setTermsChecked] = useState<boolean>(false);
  const [algoDeposit, setAlgoDeposit] = useState<number>(MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE + MBR_USER_BOX);
  const [nodeRunnerFee, setNodeRunnerFee] = useState<bigint>(0n);
  const [maxStakeAdjusted, setMaxStakeAdjusted] = useState<bigint>(0n);

  const [possibleReward, setPossibleReward] = useState<bigint | undefined>(undefined);

  // Get possible reward estimation
  useEffect(() => {
    const fetch = async () => {
      try {
        if(user && stakeReqs && stakingData){
          const currentRound = await ParamsCache.getRound();
          const returnRate = estimateRateForRounds(currentRound, stakingData.stakeOnline, stakeReqs.duration) /100;
          const possibleReward = BigInt( Math.floor( Number(user.algo) * returnRate));
          setPossibleReward(possibleReward);
        }
      } catch (error) {
        console.error('Error fetching estimating possilbe reward:', error);
      }
    }

    fetch();
  }, [stakingData, user, stakeReqs]);

  // const partnerInfo = await PartnerInfo.getUserInfo(
  //   algorandClient.client.algod,
  //   partnerAddress,
  // ); //Cache??
  const partner = undefined;

  useEffect(() => {
    //Get node runner fee and adjust maxStake according to gratis
    if (stakeReqs && gsValAd) {
      const maxStakeAdjusted = adjustedMaxStakeForGratis(stakeReqs, gsValAd);
      setMaxStakeAdjusted(maxStakeAdjusted);
      const fee = calculateNodeRunnerFee(stakeReqs, gsValAd);
      setNodeRunnerFee(fee);
    } else {
      setMaxStakeAdjusted(0n);
      setNodeRunnerFee(0n);
    }
  }, [stakeReqs, gsValAd]);

  useEffect(() => {
    //Get user role
    if (user) {
      if(user.userInfo) {
        const role = new TextDecoder().decode(new Uint8Array(user.userInfo.role));
        setRole(role);
        setAlgoDeposit(MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE);
      } else {
        setRole("");
        setAlgoDeposit(MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE + MBR_USER_BOX);
      }
    } else {
      setRole("");
      setAlgoDeposit(MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE + MBR_USER_BOX);
    }
  }, [activeAddress]);

  const handleConclude = async () => {
    console.log("Submit txn");

    if(role === ""){
      try {
        const res = await userCreateAndContractCreate({
          algorandClient: algorandClient,
          noticeBoardClient: noticeboardApp.client,
          gsNoticeBoard: noticeboardApp!.globalState!,
          gsValidatorAd: gsValAd,
          userAddress: activeAddress!,
          maxStake: maxStakeAdjusted,
          duration: stakeReqs.duration,
          delBeneficiary: activeAddress!,
          partner: partner,
          signer: transactionSigner,
        });

        if(res.returns[2]){
          console.log("Created contract with ID: " + res.returns[2]);
          console.log(res.transactions[0].txID());

          // // Fetch userInfo
          // const userInfo = await UserInfo.getUserInfo(algorandClient.client.algod, activeAddress!);
          // setUser({ ...user!, userInfo: userInfo });

          setDelAppId(res.returns[2]);
          setRefetch(true);
        }
      } catch (error) {
        console.error("Error in submit:", error);
      }
    } else {
      try {

        const res = await contractCreate({
          algorandClient: algorandClient,
          noticeBoardClient: noticeboardApp.client,
          gsNoticeBoard: noticeboardApp!.globalState!,
          gsValidatorAd: gsValAd,
          userAddress: activeAddress!,
          maxStake: maxStakeAdjusted,
          duration: stakeReqs.duration,
          delBeneficiary: activeAddress!,
          partner: partner,
          delUserInfo: user?.userInfo!,
          signer: transactionSigner,
        });

        if(res.returns[1]){
          console.log("Created contract with ID: " + res.returns[1]);
          console.log(res.transactions[0].txID());
          notify({ title: "Contract created successfully", variant: "success" });
          // // Contract creation was successful
          // // Update userInfo without need for refetch
          // const updatedAppIds = [...user!.userInfo!.appIds];
          // const idx = user!.userInfo!.getFreeAppIndex();  // Know where it is stored
          // updatedAppIds[idx] = res.returns[1];
          // setUser({ ...user!, userInfo: new UserInfo({ ...user!.userInfo!, appIds: updatedAppIds}) });

          setDelAppId(res.returns[1]);
          setRefetch(true);
        }
      } catch (error) {
        console.error("Error in submit:", error);
        notify({ title: "Contract creation failed", variant: "error" });
      }
    }

    console.log("Submitted txn")
  }

  if(!user) return

  return (
    <div
      className={cn(
        "h-min rounded-lg bg-gradient-to-br from-gradient-light to-gradient-dark p-3",
        className,
      )}
    >
      <h1 className="my-1 text-base font-bold">Contract Summary</h1>
      <Separator />
      <div className="my-3 space-y-1">
        <InfoItem>
          <InfoLabel>Contract for address:</InfoLabel>
          <InfoValue>{ellipseAddress(user.address)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Your current stake:</InfoLabel>
          <InfoValue>{algoBigIntToDisplay(user.algo, "floor", true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>
            Max stake <ITooltip value={ToolTips.MaxStake} /> :
          </InfoLabel>
          <InfoValue>{algoBigIntToDisplay(calculateGivenMaxStake(maxStakeAdjusted, gsValAd), "floor", true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>
            Algorand rewards <ITooltip value={ToolTips.AlgorandRewards} /> :
          </InfoLabel>
          <InfoValue>{stakingData ? (stakingData.apy.toFixed(APY_DECIMALS) + "%") : "N/A"}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>
            Possible reward <ITooltip value={ToolTips.PossibleRewards} /> :
          </InfoLabel>
          <InfoValue>
            {possibleReward ? algoBigIntToDisplay(possibleReward, "floor", true) : "N/A"}
          </InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Duration:</InfoLabel>
          <InfoValue>{roundsToDuration(stakeReqs.duration, TimeParams.stake, true)}</InfoValue>
        </InfoItem>
      </div>
      <Separator />
      <div className="my-3 space-y-1">
        <InfoItem className="justify-between">
          <InfoLabel>
            Node runner fee <ITooltip value={ToolTips.NodeRunnerFee} /> :
          </InfoLabel>
          <InfoValue>{assetAmountToFeeDisplay(nodeRunnerFee, stakeReqs.currency, AssetParams.total, true)}</InfoValue>
        </InfoItem>
        {partner && <InfoItem className="justify-between">
          <InfoLabel>
            {partner} convenience fee <ITooltip value={ToolTips.ConvenienceFee} /> :
          </InfoLabel>
          <InfoValue>{"TBD" + " " + CURRENCIES.get(stakeReqs.currency)!.ticker}</InfoValue>
        </InfoItem>}
        <InfoItem className="justify-between">
          <InfoLabel>
            Algorand deposit <ITooltip value={role==="" ? ToolTips.AlgorandDepositUserAndDel : ToolTips.AlgorandDepositDel} /> :
          </InfoLabel>
          <InfoValue>{algoBigIntToDisplay(BigInt(algoDeposit), "none", true, ALGORAND_DEPOSIT_DECIMALS)}</InfoValue>
        </InfoItem>
      </div>
      <Separator />
      <div className="my-3">
        <InfoItem className="justify-between">
          <InfoLabel className="text-xl text-text">Total price:</InfoLabel>
          <InfoValue className="text-xl">{assetAmountToFeeDisplay(nodeRunnerFee, stakeReqs.currency, AssetParams.total, true)}</InfoValue>
        </InfoItem>
      </div>
      <div className="mt-6 space-y-3">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="terms"
            onCheckedChange={(v) =>
              setTermsChecked(v === "indeterminate" ? false : v)
            }
          />
          <Label htmlFor="terms" className="text-sm">
            I have read, understand, and agree with <TermsAndConditions terms={TC_LATEST}/>.
          </Label>
        </div>
        <Button
          variant={"v_primary"}
          className="w-full"
          disabled={!termsChecked}
          onClick={handleConclude}
        >
          Conclude Contract & Pay
        </Button>
      </div>
    </div>
  );
};

export default ContractCreateCard;
