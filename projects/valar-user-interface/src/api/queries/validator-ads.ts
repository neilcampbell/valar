import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import AlgodClient from "algosdk/dist/types/client/v2/algod/algod";

import { UserInfo } from "@/interfaces/contracts/User";
import { ABITupleType, ABIUintType, getApplicationAddress } from "algosdk";
import { Earning } from "@/lib/types";
import { BoxUtils } from "@/utils/contract/box-utils";
import { bigIntToBytes } from "@/utils/convert";
import { ASA_ID_ALGO, BOX_ASA_KEY_PREFIX } from "@/constants/smart-contracts";

export async function fetchValOwnerAds(
  algodClient: AlgodClient,
  validatorOwnerUserInfo: UserInfo,
): Promise<Map<bigint, ValidatorAdGlobalState> | undefined>   {

  try{
    const valAdIds: bigint[] = [...validatorOwnerUserInfo.appIds.filter((id) => id != 0n)]
    const valAdsMap = fetchValidatorAds(algodClient, valAdIds)
    return valAdsMap;
  } catch {
    return undefined
  }
}

export async function fetchValidatorAds(
  algodClient: AlgodClient,
  valAdIds: bigint[],
): Promise<Map<bigint, ValidatorAdGlobalState> | undefined>   {

  const valAdsMap: Map<bigint, ValidatorAdGlobalState> = new Map();
  for (let id of valAdIds) {
    const ad = await ValidatorAdGlobalState.getGlobalState(algodClient, id);
    if (ad) {
      valAdsMap.set(ad.appId, ad);
    }
  }

  return valAdsMap;
}

export async function fetchValEarnings(
  algodClient: AlgodClient,
  gsValAd: ValidatorAdGlobalState,
): Promise<Earning[]>   {

  const abi = new ABITupleType([
    new ABIUintType(64), //total_earning
    new ABIUintType(64), //total_fees_generated
  ]);

  const valAdAddr = getApplicationAddress(gsValAd.appId);
  const res = await algodClient.accountInformation(valAdAddr).do();
  const assets = res["assets"];

  const earnings: Earning[] = [{
    id: ASA_ID_ALGO,
    total: gsValAd.totalAlgoEarned,
    unclaimed: BigInt(res["amount"] - res["min-balance"]),
  }];

  for (const asset of assets) {
    const assetId = BigInt(asset["asset-id"])
    const assetBox = await BoxUtils.getAppBox(algodClient, Number(gsValAd.appId), new Uint8Array([...BOX_ASA_KEY_PREFIX, ...bigIntToBytes(assetId, 8)]));

    if(!assetBox.exists) continue;

    const d = abi.decode(assetBox.value) as [bigint, bigint];

    const unclaimed = asset["amount"];
    earnings.push({
      id: assetId,
      total: d[0],
      unclaimed: unclaimed,
    });
  }

  return earnings;
}
