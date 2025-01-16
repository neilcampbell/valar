import AdStatus from "@/components/Status/AdStatus";
import {
  InfoItem,
  InfoLabel,
  InfoValue,
} from "@/components/Info/InfoUtilsCompo";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { ValAdStatus } from "@/lib/types";
import { useState, useEffect } from "react";
import { bytesToHex, decodeValAdState, ellipseAddress } from "@/utils/convert";
import TermsAndConditions from "@/components/TermsAndConditions/TermsAndConditions";

type ValAdInfo = {
  appId: string;
  nodeRunner: string;
  status: ValAdStatus;
  tc: string;
};

function getValAdInfo(
  va: ValidatorAdGlobalState,
): ValAdInfo {

  const status = decodeValAdState(va.state);
  const nodeRunner = ellipseAddress(va.valOwner);

  return ({
    appId: va.appId.toString(),
    nodeRunner: nodeRunner,
    status: status,
    tc: bytesToHex(va.tcSha256),
  }) as ValAdInfo;
}


const InfoCard = ({
  gsValAd,
}: {
  gsValAd: ValidatorAdGlobalState,
}) => {
  const [data, setData] = useState<ValAdInfo | undefined>(undefined);

  useEffect(() => {
    const data = getValAdInfo(gsValAd);
    setData(data);
  }, [gsValAd]);

  if(!data) return

  return (
    <div className="space-y-1 rounded-lg border border-border bg-background-light p-3">
      <h1 className="text-sm font-semibold">Main Information</h1>
      <InfoItem className="flex gap-1 text-sm">
        <InfoLabel>Ad ID:</InfoLabel>
        <InfoValue className="text-secondary">{data.appId}</InfoValue>
      </InfoItem>
      <InfoItem className="flex gap-1 text-sm">
        <InfoLabel>Node runner:</InfoLabel>
        <InfoValue className="text-secondary">{data.nodeRunner}</InfoValue>
      </InfoItem>
      <InfoItem className="flex gap-1 text-sm">
        <InfoLabel>Status:</InfoLabel>
        <InfoValue>
          <AdStatus status={data.status} />
        </InfoValue>
      </InfoItem>
      <div>
        <div className="mt-6 text-sm text-text-tertiary">
          Accepted <TermsAndConditions terms={data.tc}/>
        </div>
      </div>
    </div>
  );
};

export default InfoCard;
