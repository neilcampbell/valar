import ITooltip from "@/components/Tooltip/ITooltip";

import { InfoSection, InfoHeading, InfoItem, InfoLabel, InfoValue } from "@/components/Info/InfoUtilsCompo";
import { EligibilitySectionType } from "../../_types/types";

const EligibilitySection = ({
  data,
}: {
  data: EligibilitySectionType;
}) => {
  // Leave out section if there is no eligibility requirement
  const notGated = data.asa1Id === 0n && data.asa2Id === 0n;
  if(notGated) return;

  return (
    <InfoSection>
      <InfoHeading>Eligibility requirements</InfoHeading>
      <InfoItem>
        <InfoLabel>
          Amount of ASA1 <ITooltip />:
        </InfoLabel>
        <InfoValue>{data.asa1Amount.toString()}</InfoValue>
        <InfoValue> (ID: {data.asa1Id.toString()}) </InfoValue>
      </InfoItem>
      <InfoItem>
        <InfoLabel>
          Amount of ASA2 <ITooltip />:
        </InfoLabel>
        <InfoValue>{data.asa2Amount.toString()}</InfoValue>
        <InfoValue> (ID: {data.asa2Id.toString()}) </InfoValue>
      </InfoItem>
    </InfoSection>
  );
};

export default EligibilitySection;
