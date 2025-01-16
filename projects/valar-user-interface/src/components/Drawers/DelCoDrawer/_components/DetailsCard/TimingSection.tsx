import ITooltip from "@/components/Tooltip/ITooltip";

import { InfoSection, InfoHeading, InfoItem, InfoLabel, InfoValue } from "@/components/Info/InfoUtilsCompo";
import { TimingSectionTypeContract } from "../../_types/types";
import { roundsToDuration } from "@/utils/convert";
import { ToolTips } from "@/constants/tooltips";
import { ValTermsTimingInterface } from "@/interfaces/contracts/ValidatorAd";
import { TimeParams } from "@/constants/units";

const TimingSection = ({
  data,
}: {
  data: TimingSectionTypeContract | ValTermsTimingInterface;
}) => {

  if("roundsDurationMin" in data){
    return (
      <InfoSection>
        <InfoHeading>Timings</InfoHeading>
        <InfoItem>
          <InfoLabel>Valid until:</InfoLabel>
          <InfoValue>{data.roundMaxEnd.toString()}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>
            Setup time <ITooltip value={ToolTips.SetupTime} /> :
          </InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsSetup, TimeParams.setup, true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>
            Confirmation time <ITooltip value={ToolTips.ConfirmationTime} /> :
          </InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsConfirm, TimeParams.confirmation, true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Min contract duration:</InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsDurationMin, TimeParams.stake, true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Max contract duration:</InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsDurationMax, TimeParams.stake, true)}</InfoValue>
        </InfoItem>
      </InfoSection>
    );
  } else {
    return (
      <InfoSection>
        <InfoHeading className="text-sm font-semibold">Timings</InfoHeading>
        <InfoItem>
          <InfoLabel className="text-sm font-medium">
            Setup time <ITooltip value={ToolTips.SetupTime} /> :
          </InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsSetup, TimeParams.setup, true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel className="text-sm font-medium">
            Confirmation time <ITooltip value={ToolTips.ConfirmationTime} /> :
          </InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsConfirm, TimeParams.confirmation, true)}</InfoValue>
        </InfoItem>
      </InfoSection>
    );
  }


};

export default TimingSection;
