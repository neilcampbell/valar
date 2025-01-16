import IdenticonAvatar from "@/components/Identicon/Identicon";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Separator } from "@/components/ui/separator";
import {
  InfoItem,
  InfoLabel,
  InfoSection,
  InfoValue,
} from "@/components/Info/InfoUtilsCompo";
import { cn } from "@/lib/shadcn-utils";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import EligibilitySection from "./EligibilitySection";
import WarningsSection from "./WarningsSection";
import StakeLimitsSection from "./StakeLimitSection";
import PricingSection from "./PricingSection";
import TimingSection from "./TimingSection";
import { DataSectionsType } from "../../_types/types";
import { calculateNodeRunnerFee } from "@/utils/contract/helpers";
import { StakeReqs } from "@/lib/types";

const DetailsCard: React.FC<{
  gsDelCo: DelegatorContractGlobalState | undefined,
  gsValAd: ValidatorAdGlobalState,
  stakeReqs?: StakeReqs,
  className?: string,
 }> = ({
  gsDelCo,
  gsValAd,
  stakeReqs,
  className,
}) => {
  const [openTerms, setOpenTerms] = useState<boolean>(true);

  let sectionData: DataSectionsType | undefined = undefined;
  if(gsDelCo){
    // If Delegator Contract info is defined, it will be displayed.
    sectionData = {
      pricing: {
        currency: gsDelCo.delegationTermsGeneral.feeAssetId,
        setupFee: gsDelCo.delegationTermsGeneral.feeSetup,
        operationalFee: gsDelCo.delegationTermsGeneral.feeRound,
      },
      stakeLimits: undefined,
      warnings: {
        cntWarningMax: gsDelCo.delegationTermsBalance.cntBreachDelMax,
        roundsWarning: gsDelCo.delegationTermsBalance.roundsBreach,
      },
      timings: {
        roundsSetup: gsDelCo.delegationTermsGeneral.roundsSetup,
        roundsConfirm: gsDelCo.delegationTermsGeneral.roundsConfirm,
      },
      eligibility: {
        asa1Id: gsDelCo.delegationTermsBalance.gatingAsaList[0][0],
        asa1Amount: gsDelCo.delegationTermsBalance.gatingAsaList[0][1],
        asa2Id: gsDelCo.delegationTermsBalance.gatingAsaList[1][0],
        asa2Amount: gsDelCo.delegationTermsBalance.gatingAsaList[1][1],
      },
    }
  } else {
    // If no Delegator Contract info is defined, data based on Validator Ad will be displayed.
    if(stakeReqs){
      // If staking requirements are known, tailored data
      sectionData = {
        pricing: {
          currency: gsValAd.termsPrice.feeAssetId,
          setupFee: gsValAd.termsPrice.feeSetup,
          operationalFee: calculateNodeRunnerFee(stakeReqs, gsValAd) - gsValAd.termsPrice.feeSetup,
        },
        stakeLimits: undefined,
        warnings: gsValAd.termsWarn,
        timings: {
          roundsSetup: gsValAd.termsTime.roundsSetup,
          roundsConfirm: gsValAd.termsTime.roundsConfirm,
        },
        eligibility: {
          asa1Id: gsValAd.termsReqs.gatingAsaList[0][0],
          asa1Amount: gsValAd.termsReqs.gatingAsaList[0][1],
          asa2Id: gsValAd.termsReqs.gatingAsaList[1][0],
          asa2Amount: gsValAd.termsReqs.gatingAsaList[1][1],
        },
      }
    } else {
      sectionData = {
        pricing: gsValAd.termsPrice,
        stakeLimits: gsValAd.termsStake,
        warnings: gsValAd.termsWarn,
        timings: gsValAd.termsTime,
        eligibility: {
          asa1Id: gsValAd.termsReqs.gatingAsaList[0][0],
          asa1Amount: gsValAd.termsReqs.gatingAsaList[0][1],
          asa2Id: gsValAd.termsReqs.gatingAsaList[1][0],
          asa2Amount: gsValAd.termsReqs.gatingAsaList[1][1],
        },
      }
    }
  }

  return (
    <div className={cn("", className)} >
      <h1 className="my-1 text-base font-bold">Node Runner Details</h1>
      <Separator />
      <div className="flex justify-between py-3">
        <div className="">
          <InfoSection>
            <InfoItem>
              <InfoLabel>Node runner:</InfoLabel>
              <InfoValue>{gsValAd.valOwner}</InfoValue>
            </InfoItem>
            <InfoItem>
              <InfoLabel>Ad ID:</InfoLabel>
              <InfoValue>{gsValAd.appId.toString()}</InfoValue>
            </InfoItem>
            <InfoItem>
              <InfoLabel>Occupation:</InfoLabel>
              <InfoValue>{gsValAd.cntDel + "/" + gsValAd.cntDelMax}</InfoValue>
            </InfoItem>
          </InfoSection>
        </div>
        <div className="flex-shrink-0">
          <IdenticonAvatar value={"test"} className="h-10 w-10" />
        </div>
      </div>
      <Collapsible open={openTerms} onOpenChange={setOpenTerms}>
        <div className="flex justify-between">
          <h4 className="text-sm font-bold">Node runner terms</h4>
          <CollapsibleTrigger>
            {openTerms ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
            <span className="sr-only">Toggle</span>
          </CollapsibleTrigger>
        </div>
        <CollapsibleContent className="mt-3 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="flex flex-col justify-between gap-6">
            <PricingSection data={sectionData.pricing}/>
            <StakeLimitsSection data={sectionData.stakeLimits}/>
            <WarningsSection data={sectionData.warnings}/>
          </div>
          <div className="flex flex-col gap-6">
            <TimingSection data={sectionData.timings}/>
            <EligibilitySection data={sectionData.eligibility}/>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
};

export default DetailsCard;
