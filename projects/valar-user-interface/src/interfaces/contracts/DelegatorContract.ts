import { DelegatorContractClient } from "@/contracts/DelegatorContract";
import {
  ABIAddressType,
  ABIArrayStaticType,
  ABIBoolType,
  ABITupleType,
  ABIUintType,
} from "algosdk";
import AlgodClient from "algosdk/dist/types/client/v2/algod/algod";

/**
 * =======================================
 *     Delegation Contract Global State
 * =======================================
 */

export interface DelContractGlobalStateInterface {
  appId: bigint;

  cntBreachDel: bigint;
  delBeneficiary: string;
  delManager: string;

  delegationTermsBalance: DelegationTermsBalance;
  delegationTermsGeneral: DelegationTermsGeneral;

  feeOperational: bigint;
  feeOperationalPartner: bigint;

  noticeboardAppId: bigint;
  validatorAdAppId: bigint;

  roundStart: bigint;
  roundEnd: bigint;
  roundEnded: bigint;

  voteKeyDilution: bigint;
  selKey: Uint8Array;
  voteKey: Uint8Array;
  stateProofKey: Uint8Array;

  state: Uint8Array;
  stateCur: Uint8Array;
  tcSha256: Uint8Array;

  roundBreachLast: bigint;
  roundClaimLast: bigint;
  roundExpirySoonLast: bigint;
}

export class DelegatorContractGlobalState
  implements DelContractGlobalStateInterface
{
  appId: bigint;

  noticeboardAppId: bigint;
  validatorAdAppId: bigint;

  feeOperational: bigint;
  feeOperationalPartner: bigint;

  delegationTermsBalance: DelegationTermsBalance;
  delegationTermsGeneral: DelegationTermsGeneral;

  delManager: string;
  delBeneficiary: string;

  roundBreachLast: bigint;
  roundClaimLast: bigint;
  roundEnd: bigint;
  roundEnded: bigint;
  roundExpirySoonLast: bigint;
  roundStart: bigint;

  selKey: Uint8Array;
  stateProofKey: Uint8Array;
  voteKeyDilution: bigint;
  voteKey: Uint8Array;

  state: Uint8Array;
  stateCur: Uint8Array;

  tcSha256: Uint8Array;

  cntBreachDel: bigint;

  constructor({
    appId,
    noticeboardAppId,
    validatorAdAppId,
    feeOperational,
    feeOperationalPartner,
    delegationTermsBalance,
    delegationTermsGeneral,
    delManager,
    delBeneficiary,
    roundStart,
    roundEnd,
    roundEnded,
    voteKeyDilution,
    selKey,
    voteKey,
    stateProofKey,
    state,
    stateCur,
    tcSha256,
    cntBreachDel,
    roundBreachLast,
    roundClaimLast,
    roundExpirySoonLast,
  }: DelContractGlobalStateInterface) {
    this.appId = appId;
    this.noticeboardAppId = noticeboardAppId;
    this.validatorAdAppId = validatorAdAppId;

    this.feeOperational = feeOperational;
    this.feeOperationalPartner = feeOperationalPartner;

    this.delegationTermsBalance = delegationTermsBalance;
    this.delegationTermsGeneral = delegationTermsGeneral;

    this.delManager = delManager;
    this.delBeneficiary = delBeneficiary;

    this.roundStart = roundStart;
    this.roundEnd = roundEnd;
    this.roundEnded = roundEnded;

    this.voteKeyDilution = voteKeyDilution;
    this.selKey = selKey;
    this.voteKey = voteKey;
    this.stateProofKey = stateProofKey;

    this.state = state;
    this.stateCur = stateCur;
    this.tcSha256 = tcSha256;

    this.cntBreachDel = cntBreachDel;
    this.roundBreachLast = roundBreachLast;
    this.roundClaimLast = roundClaimLast;
    this.roundExpirySoonLast = roundExpirySoonLast;
  }

  static async getGlobalState(
    algodClient: AlgodClient,
    delAppID: bigint,
  ): Promise<DelegatorContractGlobalState | undefined> {
    try {
      const delClient = new DelegatorContractClient(
        {
          resolveBy: "id",
          id: delAppID,
        },
        algodClient,
      );

      const gs = await delClient.getGlobalState();

      return {
        appId: delAppID,

        noticeboardAppId: gs.noticeboardAppId!.asBigInt(),
        validatorAdAppId: gs.validatorAdAppId!.asBigInt(),

        delegationTermsGeneral: DelegationTermsGeneral.decodeBytes(
          gs.g!.asByteArray(),
        ),
        delegationTermsBalance: DelegationTermsBalance.decodeBytes(
          gs.b!.asByteArray(),
        ),

        feeOperational: gs.feeOperational!.asBigInt(),
        feeOperationalPartner: gs.feeOperationalPartner!.asBigInt(),

        delManager: new ABIAddressType().decode(gs.delManager!.asByteArray()),
        delBeneficiary: new ABIAddressType().decode(
          gs.delBeneficiary!.asByteArray(),
        ),

        roundStart: gs.roundStart!.asBigInt(),
        roundEnd: gs.roundEnd!.asBigInt(),
        roundEnded: gs.roundEnded!.asBigInt(),

        voteKeyDilution: gs.voteKeyDilution!.asBigInt(),
        selKey: gs.selKey!.asByteArray(),
        voteKey: gs.voteKey!.asByteArray(),
        stateProofKey: gs.stateProofKey!.asByteArray(),

        state: gs.state!.asByteArray(),
        stateCur: gs.state!.asByteArray(),
        tcSha256: gs.tcSha256!.asByteArray(),

        cntBreachDel: gs.cntBreachDel!.asBigInt(),
        roundBreachLast: gs.roundBreachLast!.asBigInt(),
        roundClaimLast: gs.roundClaimLast!.asBigInt(),
        roundExpirySoonLast: gs.roundExpirySoonLast!.asBigInt(),
      };
    } catch (err) {
      return undefined;
    }
  }
}

/**
 * =================================
 *     Delegation Terms General
 * =================================
 */

export interface DelegationTermsGeneralInterface {
  commission: bigint;
  feeRound: bigint;
  feeSetup: bigint;
  feeAssetId: bigint;
  partnerAddress: string;
  feeRoundPartner: bigint;
  feeSetupPartner: bigint;
  roundsSetup: bigint;
  roundsConfirm: bigint;
}

export type DelegationTermsGeneralArray = [
  bigint,
  bigint,
  bigint,
  bigint,
  string,
  bigint,
  bigint,
  bigint,
  bigint,
];

export class DelegationTermsGeneral implements DelegationTermsGeneralInterface {
  commission: bigint;
  feeRound: bigint;
  feeSetup: bigint;
  feeAssetId: bigint;
  partnerAddress: string;
  feeRoundPartner: bigint;
  feeSetupPartner: bigint;
  roundsSetup: bigint;
  roundsConfirm: bigint;

  static readonly abi = new ABITupleType([
    new ABIUintType(64), //Commission
    new ABIUintType(64), //FeeRound
    new ABIUintType(64), //FeeSetup
    new ABIUintType(64), //FeeAssetId
    new ABIAddressType(), //PartnerAddress
    new ABIUintType(64), //FeeRoundPartner
    new ABIUintType(64), //FeeSetupPartner
    new ABIUintType(64), //RoundsSetup
    new ABIUintType(64), //RoundsConfirm
  ]);

  constructor({
    commission,
    feeRound,
    feeSetup,
    feeAssetId,
    partnerAddress,
    feeRoundPartner,
    feeSetupPartner,
    roundsSetup,
    roundsConfirm,
  }: DelegationTermsGeneralInterface) {
    this.commission = commission;
    this.feeRound = feeRound;
    this.feeSetup = feeSetup;
    this.feeAssetId = feeAssetId;
    this.partnerAddress = partnerAddress;
    this.feeRoundPartner = feeRoundPartner;
    this.feeSetupPartner = feeSetupPartner;
    this.roundsSetup = roundsSetup;
    this.roundsConfirm = roundsConfirm;
  }

  static decodeBytes(data: Uint8Array): DelegationTermsGeneral {
    const d = this.abi.decode(data) as DelegationTermsGeneralArray;

    return new DelegationTermsGeneral({
      commission: d[0],
      feeRound: d[1],
      feeSetup: d[2],
      feeAssetId: d[3],
      partnerAddress: d[4],
      feeRoundPartner: d[5],
      feeSetupPartner: d[6],
      roundsSetup: d[7],
      roundsConfirm: d[8],
    });
  }

  static encodeArray(
    data: DelegationTermsGeneral | DelegationTermsGeneralInterface,
  ): DelegationTermsGeneralArray {
    const {
      commission,
      feeRound,
      feeSetup,
      feeAssetId,
      partnerAddress,
      feeRoundPartner,
      feeSetupPartner,
      roundsSetup,
      roundsConfirm,
    } = data;

    return [
      commission,
      feeRound,
      feeSetup,
      feeAssetId,
      partnerAddress,
      feeRoundPartner,
      feeSetupPartner,
      roundsSetup,
      roundsConfirm,
    ];
  }
}

/**
 * =================================
 *     Delegation Terms Balance
 * =================================
 */

export interface DelegationTermsBalanceInterface {
  stakeMax: bigint;
  cntBreachDelMax: bigint;
  roundsBreach: bigint;
  gatingAsaList: [[bigint, bigint], [bigint, bigint]];
}

export type DelegationTermsBalanceArray = [
  bigint,
  bigint,
  bigint,
  [[bigint, bigint], [bigint, bigint]],
];

export class DelegationTermsBalance implements DelegationTermsBalanceInterface {
  stakeMax: bigint;
  cntBreachDelMax: bigint;
  roundsBreach: bigint;
  gatingAsaList: [[bigint, bigint], [bigint, bigint]];

  static readonly abi = new ABITupleType([
    new ABIUintType(64), //stake
    new ABIUintType(64), //cnt_breach_del_max
    new ABIUintType(64), //rounds_breach
    new ABIArrayStaticType(new ABIArrayStaticType(new ABIUintType(64), 2), 2), //gating_asa_list
  ]);

  constructor({
    stakeMax,
    cntBreachDelMax,
    roundsBreach,
    gatingAsaList,
  }: DelegationTermsBalanceInterface) {
    this.stakeMax = stakeMax;
    this.cntBreachDelMax = cntBreachDelMax;
    this.roundsBreach = roundsBreach;
    this.gatingAsaList = gatingAsaList;
  }

  static decodeBytes(data: Uint8Array): DelegationTermsBalance {
    const d = this.abi.decode(data) as DelegationTermsBalanceArray;

    return new DelegationTermsBalance({
      stakeMax: d[0],
      cntBreachDelMax: d[1],
      roundsBreach: d[2],
      gatingAsaList: d[3],
    });
  }

  static encodeArray(
    data: DelegationTermsBalance | DelegationTermsBalanceInterface,
  ): DelegationTermsBalanceArray {
    const { stakeMax, cntBreachDelMax, roundsBreach, gatingAsaList } = data;

    return [stakeMax, cntBreachDelMax, roundsBreach, gatingAsaList];
  }
}
