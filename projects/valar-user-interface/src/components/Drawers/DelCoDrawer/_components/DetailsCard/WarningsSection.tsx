import ITooltip from "@/components/Tooltip/ITooltip";

import { InfoSection, InfoHeading, InfoItem, InfoLabel, InfoValue } from "@/components/Info/InfoUtilsCompo";
import { ToolTips } from "@/constants/tooltips";
import { roundsToDuration } from "@/utils/convert";
import { ValTermsWarningsInterface } from "@/interfaces/contracts/ValidatorAd";
import { TimeParams } from "@/constants/units";

const WarningsSection = ({
  data,
}: {
  data: ValTermsWarningsInterface;
}) => {
  return (
    <InfoSection>
      <InfoHeading className="text-sm font-semibold">Warnings</InfoHeading>
      <InfoItem>
        <InfoLabel className="text-sm font-medium">
          Max warnings <ITooltip value={ToolTips.MaxWarnings}/>:
        </InfoLabel>
        <InfoValue>{Number(data.cntWarningMax,)}</InfoValue>
      </InfoItem>
      <InfoItem>
        <InfoLabel className="text-sm font-medium">
          Warning time <ITooltip value={ToolTips.WarningTime}/>:
        </InfoLabel>
        <InfoValue>{roundsToDuration(data.roundsWarning, TimeParams.warn, true)}</InfoValue>
      </InfoItem>
    </InfoSection>
  );
};

export default WarningsSection;
