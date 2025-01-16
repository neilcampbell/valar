import ITooltip from "@/components/Tooltip/ITooltip";

import { InfoSection, InfoHeading, InfoItem, InfoLabel, InfoValue } from "@/components/Info/InfoUtilsCompo";
import { PricingSectionTypeContract } from "../../_types/types";
import { CURRENCIES } from "@/constants/platform";
import { assetAmountToFeeDisplay } from "@/utils/convert";
import { ToolTips } from "@/constants/tooltips";
import { ValTermsPricingInterface } from "@/interfaces/contracts/ValidatorAd";
import { AssetParams } from "@/constants/units";

const PricingSection = ({
  data,
}: {
  data: PricingSectionTypeContract | ValTermsPricingInterface;
}) => {


  if("operationalFee" in data){
    const ticker: string = CURRENCIES.get(data.currency)!.ticker || "Unknown";

    return (
      <InfoSection>
        <InfoHeading className="text-sm font-semibold">Fees</InfoHeading>
        <InfoItem>
          <InfoLabel className="text-sm font-medium">Payment currency:</InfoLabel>
          <InfoValue>{ticker}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel className="text-sm font-medium">
            Setup fee <ITooltip value={ToolTips.SetupFee}/>:
          </InfoLabel>
          <InfoValue>{assetAmountToFeeDisplay(data.setupFee, data.currency, AssetParams.setup, true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel className="text-sm font-medium">
            Operational fee <ITooltip value={ToolTips.OperationalFee}/>:
          </InfoLabel>
          <InfoValue>{assetAmountToFeeDisplay(data.operationalFee, data.currency, AssetParams.opDuration, true)}</InfoValue>
        </InfoItem>
      </InfoSection>
    );
  } else {
    const ticker: string = CURRENCIES.get(data.feeAssetId)!.ticker || "Unknown";

    return (
      <InfoSection>
        <InfoHeading className="text-sm font-semibold">Fees</InfoHeading>
        <InfoItem>
          <InfoLabel>Payment currency:</InfoLabel>
          <InfoValue>{ticker}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel className="text-sm font-medium">
            Setup fee <ITooltip value={ToolTips.SetupFee}/>:
          </InfoLabel>
          <InfoValue>{assetAmountToFeeDisplay(data.feeSetup, data.feeAssetId, AssetParams.setup, true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel className="text-sm font-medium">
            Min operational fee <ITooltip value={ToolTips.MinOperationalFee}/>:
          </InfoLabel>
          <InfoValue>{assetAmountToFeeDisplay(data.feeRoundMin, data.feeAssetId, AssetParams.opMin, true) + "/month"}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel className="text-sm font-medium">
            Var operational fee <ITooltip value={ToolTips.VarOperationalFee}/>:
          </InfoLabel>
          <InfoValue>{assetAmountToFeeDisplay(data.feeRoundVar, data.feeAssetId, AssetParams.opVar, true) + "/(month*100k ALGO)"}</InfoValue>
        </InfoItem>
      </InfoSection>
    );
  }


};

export default PricingSection;
