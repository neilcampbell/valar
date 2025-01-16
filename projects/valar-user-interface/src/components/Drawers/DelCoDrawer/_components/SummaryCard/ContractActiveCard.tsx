import ITooltip from "@/components/Tooltip/ITooltip";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  InfoItem,
  InfoLabel,
  InfoValue,
} from "@/components/Info/InfoUtilsCompo";
import { cn } from "@/lib/shadcn-utils";
import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import ContractStatus from "@/components/Status/ContractStatus";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useEffect, useState } from "react";
import { DelCoStatus } from "@/lib/types";
import { algoBigIntToDisplay, bytesToHex, bytesToStr, decodeDelCoState, ellipseAddress, roundsToDate } from "@/utils/convert";
import { contractDelete, contractWithdraw, keysConfirm } from "@/api/contract/DelegatorCalls";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import useUserStore from "@/store/userStore";
import { useWallet } from "@txnlab/use-wallet-react";
import WithdrawContractPopup from "@/components/Popup/WithdrawContractPopup";
import ExtendContractPopup from "@/components/Popup/ExtendContractPopup";
import { ParamsCache } from "@/utils/paramsCache";
import { DC_STATE_ENDED_MASK, DC_STATE_LIVE, DC_STATE_READY, DC_STATE_SUBMITTED } from "@/constants/states";
import { FROM_BASE_TO_MILLI_MULTIPLIER } from "@/constants/units";
import { ASSUMED_BLOCK_TIME } from "@/constants/timing";
import TermsAndConditions from "@/components/TermsAndConditions/TermsAndConditions";
import { DateToFormDisplay } from "@/lib/utils";
import { UserInfo } from "@/interfaces/contracts/User";
import { notify } from "@/components/Notification/notification";

type DelCoSummary = {
  delBeneficiary: string;
  contractId: string;
  status: DelCoStatus;
  contractStart: string;
  contractEnd: string;
  yourStake: string;
  maxStake: string;
  warned: boolean;
  warnings: string;
  lastWarning: string;
  tc: string;
};

async function getDelCoSummary(
  gsDelCo: DelegatorContractGlobalState,
  yourStake: bigint,
): Promise<DelCoSummary> {

  const { status } = decodeDelCoState(gsDelCo.stateCur);

  const delBeneficiary = ellipseAddress(gsDelCo.delBeneficiary);
  const contractStart = DateToFormDisplay(await roundsToDate(gsDelCo.roundStart));
  const contractEnd = DateToFormDisplay(await roundsToDate(gsDelCo.roundEnd));
  const _yourStake = algoBigIntToDisplay(yourStake, "floor", true);
  const maxStake = algoBigIntToDisplay(gsDelCo.delegationTermsBalance.stakeMax, "floor", true);
  const warnings = gsDelCo.cntBreachDel;
  const maxWarnings = gsDelCo.delegationTermsBalance.cntBreachDelMax;
  const lastWarning = gsDelCo.roundBreachLast.toString();

  let warned = false;
  if(warnings > 0n){
    warned = true;
  }

  return ({
    delBeneficiary: delBeneficiary,
    contractId: gsDelCo.appId.toString(),
    status: status,
    contractStart: contractStart,
    contractEnd: contractEnd,
    yourStake: _yourStake,
    maxStake: maxStake,
    warned: warned,
    warnings: warnings.toString() + "/" + maxWarnings.toString(),
    lastWarning: lastWarning,
    tc: bytesToHex(gsDelCo.tcSha256),
  }) as DelCoSummary;
}

const Actions: React.FC<{
  gsDelCo: DelegatorContractGlobalState,
  gsValAd: ValidatorAdGlobalState,
  drawerClose: () => void,
  setRefetch: React.Dispatch<React.SetStateAction<boolean>>,
}> = ({
  gsDelCo,
  gsValAd,
  drawerClose,
  setRefetch,
}) => {
  const { algorandClient, noticeboardApp } = useAppGlobalState();
  const { activeAddress, transactionSigner } = useWallet();
  const { user } = useUserStore();

  const [openWithdrawPopup, setOpenWithdrawPopup] = useState<boolean>(false);
  const [openExtendPopup, setOpenExtendPopup] = useState<boolean>(false);

  // ------------------------------------------
  // ------------------------------------------
  // --- Handles for action buttons onClick ---
  // ------------------------------------------
  // ------------------------------------------
  const handleConfirmSetup = async () => {
    console.log("Submitting txn to confirm setup...");

    try {
      const userInfo = await UserInfo.getUserInfo(
        algorandClient.client.algod,
        activeAddress!,
      );

      const res = await keysConfirm({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsValAd,
        gsDelCo,
        userAddress: activeAddress!,
        user: { ...user!, userInfo: userInfo },
        signer: transactionSigner,
      });

      if (res.transactions[0]) {
        console.log(`Confirmed keys for account ${gsDelCo.delBeneficiary} under service contract ID ${gsDelCo.appId}.`);
        console.log(res.transactions[0].txID());

        setRefetch(true);
        notify({ title: "Setup confirmed successfully", variant: "success" });
      }
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Setup confirmation failed", variant: "error" });
    }
  };

  const handleArchive = async () => {
    console.log("Submitting txn to archive contract...");

    try {
      const res = await contractDelete({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsValAd,
        gsDelCo,
        userAddress: activeAddress!,
        delUserInfo: user!.userInfo!,
        signer: transactionSigner,
      });

      if (res.transactions[0]) {
        console.log(`Archived service contract ID ${gsDelCo.appId}.`);
        console.log(res.transactions[0].txID());
        notify({ title: "Contract archived successfully", variant: "success" });

        setRefetch(true);
        drawerClose();
      }
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Contract archive failed", variant: "error" });
    }
  };

  const handleWithdraw = async () => {
    console.log("Submitting txn to withdraw from contract...");

    try {
      const res = await contractWithdraw({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsValAd,
        gsDelCo,
        userAddress: activeAddress!,
        delUserInfo: user!.userInfo!,
        delKeyRegParams: user!.keyRegParams,
        signer: transactionSigner,
      });

      if (res.transactions[0]) {
        console.log(`Withdrew from service contract ID ${gsDelCo.appId}.`);
        console.log(res.transactions[0].txID());
        notify({ title: "Contract withdrew successfully", variant: "success" });

        setRefetch(true);
      }
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Contract withdraw failed", variant: "error" });
    }
  };

  const handleExtend = async () => {
    
  };

  // ---------------------------------------
  // ---------------------------------------
  // ---       Buttons to display        ---
  // ---------------------------------------
  // ---------------------------------------

  if(bytesToStr(gsDelCo.stateCur) === bytesToStr(DC_STATE_LIVE)){
    return(
      <>
        <Button variant={"v_outline"} className="w-full text-sm" onClick={()=>setOpenWithdrawPopup(true)}>
          Withdraw from Contract
        </Button>
        <WithdrawContractPopup isOpen={openWithdrawPopup} setOpen={setOpenWithdrawPopup} handleWithdraw={handleWithdraw} delAppId={gsDelCo.appId}/>
        {/* <Button variant={"v_primary"} className="w-1/2 text-sm" onClick={()=>setOpenExtendPopup(true)}>
          Extend Contract
        </Button> */}
        <ExtendContractPopup isOpen={openExtendPopup} setOpen={setOpenExtendPopup} handleExtend={handleExtend} />
      </>
    );
  } else if(bytesToStr(gsDelCo.stateCur) === bytesToStr(DC_STATE_READY)){
    return(
      <Button variant={"v_primary"} className="w-full text-sm" disabled={true} >
        Confirm Setup
      </Button>
    );
  } else if(bytesToStr(gsDelCo.stateCur) === bytesToStr(DC_STATE_SUBMITTED)){
    return(
      <Button variant={"v_primary"} className="w-full text-sm" onClick={handleConfirmSetup} >
        Confirm Setup
      </Button>
    );
  } else if(bytesToStr(gsDelCo.stateCur) >= bytesToStr(DC_STATE_ENDED_MASK)){
    return(
      <Button variant={"v_primary"} className="w-full text-sm" onClick={handleArchive} >
        Archive Contract
      </Button>
    );
  } else {
    // Should not be possible
    return;
  }
};

const formatTime = (secs: number) => {
  const hours = Math.floor(secs / 3600);
  const minutes = Math.floor((secs % 3600) / 60);
  const seconds = secs % 60;

  if (hours > 0) {
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
};

const ContractActiveCard: React.FC<{
  gsDelCo: DelegatorContractGlobalState,
  gsValAd: ValidatorAdGlobalState,
  yourStake: bigint,
  drawerClose: () => void,
  className?: string
  setRefetch: React.Dispatch<React.SetStateAction<boolean>>;
}> = ({
  gsDelCo,
  gsValAd,
  yourStake,
  drawerClose,
  className,
  setRefetch,
}) => {
  const { activeAddress } = useWallet();
  const [data, setData] = useState<DelCoSummary | undefined>(undefined);
  const [timeLeft, setTimeLeft] = useState<number | undefined>(undefined);
  const [extStatusText, setExtStatusText] = useState<string | undefined>(undefined);

  useEffect(() => {
    const fetch = async () => {
      // Convert data to be displayed
      const data = await getDelCoSummary(gsDelCo, yourStake)

      // Set countdown timer based on state and current round
      if(
        bytesToStr(gsDelCo.stateCur) === bytesToStr(DC_STATE_READY) ||
        bytesToStr(gsDelCo.stateCur) === bytesToStr(DC_STATE_SUBMITTED)
      ){
        const roundCur = await ParamsCache.getRound();
        let roundEnd = gsDelCo.roundStart + gsDelCo.delegationTermsGeneral.roundsSetup;
        if(bytesToStr(gsDelCo.stateCur) === bytesToStr(DC_STATE_SUBMITTED)){
          roundEnd = (gsDelCo.roundStart + gsDelCo.delegationTermsGeneral.roundsSetup + gsDelCo.delegationTermsGeneral.roundsConfirm);
        }
        const timer = Number(roundEnd - roundCur) * ASSUMED_BLOCK_TIME * FROM_BASE_TO_MILLI_MULTIPLIER;
        setTimeLeft(timer); // Initialize timer to estimated time
      } else {
        setTimeLeft(undefined);
        const { extStatusText } = decodeDelCoState(gsDelCo.stateCur);
        setExtStatusText(extStatusText);
      }
      setData(data);
    }

    fetch();
  }, [gsDelCo]);

  // Update timer
  const timerInterval = 1*FROM_BASE_TO_MILLI_MULTIPLIER; // [ms]
  useEffect(() => {
    if(timeLeft){
      if (timeLeft <= 0) {
        setExtStatusText(undefined);
        setRefetch(true);
        return;
      }

      const intervalId = setInterval(() => {
        setTimeLeft((prev) => {
          setExtStatusText(" (" + formatTime(Math.floor((prev!)/FROM_BASE_TO_MILLI_MULTIPLIER)) + ")");
          return(prev! - timerInterval);
        });
      }, timerInterval);

      return () => clearInterval(intervalId); // Clear on component unmount
    }
  }, [timeLeft]);


  if(!data) return

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
          <InfoValue>{data.delBeneficiary}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Contract ID:</InfoLabel>
          <InfoValue>{data.contractId}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Status:</InfoLabel>
          <InfoValue>
            <ContractStatus
              status={data.status}
              extStatusText={extStatusText}
            />
          </InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel className="flex items-center gap-1">
            Monitor performance <ITooltip /> :
          </InfoLabel>
          <InfoValue>
            <a target="_blank" 
              rel="noopener noreferrer" 
              className="text-secondary"
              href="https://alerts.allo.info/">https://alerts.allo.info/
            </a>
          </InfoValue>
        </InfoItem>
      </div>
      <Separator />
      <div className="my-3 space-y-1">
        <InfoItem>
          <InfoLabel>Contract start:</InfoLabel>
          <InfoValue>{data.contractStart}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Contract expiry:</InfoLabel>
          <InfoValue>{data.contractEnd}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>{activeAddress === gsDelCo.delManager ? "Your current stake:" : "Current stake:"}</InfoLabel>
          <InfoValue>{data.yourStake}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Max stake:</InfoLabel>
          <InfoValue>{data.maxStake}</InfoValue>
        </InfoItem>
        {data.warned && <div>
          <InfoItem>
            <InfoLabel>Number of warnings:</InfoLabel>
            <InfoValue>{data.warnings}</InfoValue>
          </InfoItem>
          <InfoItem>
            <InfoLabel>Latest warning:</InfoLabel>
            <InfoValue>{data.lastWarning}</InfoValue>
          </InfoItem>
        </div>}
      </div>
      <div className="mt-4 text-sm text-text-tertiary">
        Accepted <TermsAndConditions terms={data.tc}/>
      </div>
      {activeAddress === gsDelCo.delManager && (<div className="mt-10 flex gap-2">
        <Actions gsDelCo={gsDelCo} gsValAd={gsValAd} drawerClose={drawerClose} setRefetch={setRefetch}/>
      </div>)}
    </div>
  );
};

export default ContractActiveCard;
