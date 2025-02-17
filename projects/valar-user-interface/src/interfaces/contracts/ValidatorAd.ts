import { Buffer } from "buffer";
import { ValidatorAdClient } from "@/contracts/ValidatorAd";
import { bytesToStr, strToBytes } from "@/utils/convert";
import { ABIAddressType, ABIArrayStaticType, ABIByteType, ABITupleType, ABIUintType } from "algosdk";
import AlgodClient from "algosdk/dist/types/client/v2/algod/algod";

import { GlobalState, GlobalStateJSONConfig } from "./GlobalState";

/**
 * =====================================
 *     Validator Global State
 * =====================================
 */

export interface ValAdGlobalStateInterface {
  appId: bigint;

  noticeboardAppId: bigint;

  termsTime: ValTermsTiming;
  termsPrice: ValTermsPricing;
  termsStake: ValTermsStakeLimits;
  termsReqs: ValTermsGating;
  termsWarn: ValTermsWarnings;

  valOwner: string;
  valManager: string;

  valInfo: ValSelfDisclosure;

  state: Uint8Array;

  cntDel: bigint;
  cntDelMax: bigint;

  delAppList: [
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
  ];

  tcSha256: Uint8Array;

  totalAlgoEarned: bigint;
  totalAlgoFeesGenerated: bigint;

  cntAsa: bigint;
}

export class ValidatorAdGlobalState implements ValAdGlobalStateInterface {
  appId: bigint;

  noticeboardAppId: bigint;

  termsTime: ValTermsTiming;
  termsPrice: ValTermsPricing;
  termsStake: ValTermsStakeLimits;
  termsReqs: ValTermsGating;
  termsWarn: ValTermsWarnings;

  valOwner: string;
  valManager: string;

  valInfo: ValSelfDisclosure;

  state: Uint8Array;

  cntDel: bigint;
  cntDelMax: bigint;

  delAppList: [
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
    bigint,
  ];

  tcSha256: Uint8Array;

  totalAlgoEarned: bigint;
  totalAlgoFeesGenerated: bigint;

  cntAsa: bigint;

  // Constructor
  constructor({
    appId,
    noticeboardAppId,
    termsTime,
    termsPrice,
    termsStake,
    termsReqs,
    termsWarn,

    valOwner,
    valManager,
    valInfo,
    state,
    cntDel,
    cntDelMax,

    delAppList,
    tcSha256,
    totalAlgoEarned,
    totalAlgoFeesGenerated,
    cntAsa,
  }: ValAdGlobalStateInterface) {
    this.appId = appId;
    this.noticeboardAppId = noticeboardAppId;
    this.termsTime = termsTime;
    this.termsPrice = termsPrice;
    this.termsStake = termsStake;
    this.termsReqs = termsReqs;
    this.termsWarn = termsWarn;

    this.valOwner = valOwner;
    this.valManager = valManager;
    this.valInfo = valInfo;
    this.state = state;
    this.cntDel = cntDel;
    this.cntDelMax = cntDelMax;

    this.delAppList = delAppList;
    this.tcSha256 = tcSha256;
    this.totalAlgoEarned = totalAlgoEarned;
    this.totalAlgoFeesGenerated = totalAlgoFeesGenerated;
    this.cntAsa = cntAsa;
  }

  // JSON Config
  private static readonly jsonConfig: GlobalStateJSONConfig<ValAdGlobalStateInterface> = {
    noticeboard_app_id: {
      fieldName: "noticeboardAppId",
      getValue: (v) => BigInt(v.uint),
    },
    T: {
      fieldName: "termsTime",
      getValue: (v) => ValTermsTiming.decodeBytes(Buffer.from(v.bytes, "base64")),
    },
    P: {
      fieldName: "termsPrice",
      getValue: (v) => ValTermsPricing.decodeBytes(Buffer.from(v.bytes, "base64")),
    },
    S: {
      fieldName: "termsStake",
      getValue: (v) => ValTermsStakeLimits.decodeBytes(Buffer.from(v.bytes, "base64")),
    },
    G: {
      fieldName: "termsReqs",
      getValue: (v) => ValTermsGating.decodeBytes(Buffer.from(v.bytes, "base64")),
    },
    W: {
      fieldName: "termsWarn",
      getValue: (v) => ValTermsWarnings.decodeBytes(Buffer.from(v.bytes, "base64")),
    },
    V: {
      fieldName: "valInfo",
      getValue: (v) => ValSelfDisclosure.decodeBytes(Buffer.from(v.bytes, "base64")),
    },
    val_owner: {
      fieldName: "valOwner",
      getValue: (v) => new ABIAddressType().decode(Buffer.from(v.bytes, "base64")),
    },
    val_manager: {
      fieldName: "valManager",
      getValue: (v) => new ABIAddressType().decode(Buffer.from(v.bytes, "base64")),
    },
    state: {
      fieldName: "state",
      getValue: (v) => Buffer.from(v.bytes, "base64"),
    },
    cnt_del: {
      fieldName: "cntDel",
      getValue: (v) => BigInt(v.uint),
    },
    cnt_del_max: {
      fieldName: "cntDelMax",
      getValue: (v) => BigInt(v.uint),
    },
    del_app_list: {
      fieldName: "delAppList",
      getValue: (v) => DelAppList.decodeBytes(Buffer.from(v.bytes, "base64")),
    },
    tc_sha256: {
      fieldName: "tcSha256",
      getValue: (v) => Buffer.from(v.bytes, "base64"),
    },
    total_algo_earned: {
      fieldName: "totalAlgoEarned",
      getValue: (v) => BigInt(v.uint),
    },
    total_algo_fees_generated: {
      fieldName: "totalAlgoFeesGenerated",
      getValue: (v) => BigInt(v.uint),
    },
    cnt_asa: {
      fieldName: "cntAsa",
      getValue: (v) => BigInt(v.uint),
    },
  };

  // Fetch Global State
  static async getGlobalState(algodClient: AlgodClient, valAppID: bigint): Promise<ValidatorAdGlobalState | undefined> {
    try {
      const valClient = new ValidatorAdClient(
        {
          resolveBy: "id",
          id: valAppID,
        },
        algodClient,
      );

      const gs = await valClient.getGlobalState();

      return new ValidatorAdGlobalState({
        appId: valAppID,
        noticeboardAppId: gs.noticeboardAppId!.asBigInt(),
        termsTime: ValTermsTiming.decodeBytes(gs.t!.asByteArray()),
        termsPrice: ValTermsPricing.decodeBytes(gs.p!.asByteArray()),
        termsStake: ValTermsStakeLimits.decodeBytes(gs.s!.asByteArray()),
        termsReqs: ValTermsGating.decodeBytes(gs.g!.asByteArray()),
        termsWarn: ValTermsWarnings.decodeBytes(gs.w!.asByteArray()),

        valOwner: new ABIAddressType().decode(gs.valOwner!.asByteArray()),
        valManager: new ABIAddressType().decode(gs.valManager!.asByteArray()),
        valInfo: ValSelfDisclosure.decodeBytes(gs.v!.asByteArray()),
        state: gs.state!.asByteArray(),
        cntDel: gs.cntDel!.asBigInt(),
        cntDelMax: gs.cntDelMax!.asBigInt(),

        delAppList: DelAppList.decodeBytes(gs.delAppList!.asByteArray()),
        tcSha256: gs.tcSha256!.asByteArray(),
        totalAlgoEarned: gs.totalAlgoEarned!.asBigInt(),
        totalAlgoFeesGenerated: gs.totalAlgoFeesGenerated!.asBigInt(),
        cntAsa: gs.cntAsa!.asBigInt(),
      });
    } catch (err) {
      console.log(err);
      return undefined;
    }
  }

  // Fetch Global State from JSON
  static getGlobalStateFromJson(json: any): ValidatorAdGlobalState | undefined {
    try {
      const appId = BigInt(json["id"]);

      if (!json["params"]?.["global-state"]) {
        throw new Error("Invalid JSON structure: missing params.global-state");
      }

      const rawGlobalState = GlobalState.getRawGlobalStateFromJSON(
        json["params"]["global-state"],
        ValidatorAdGlobalState.jsonConfig,
      );

      return new ValidatorAdGlobalState({ ...rawGlobalState, appId } as ValAdGlobalStateInterface);
    } catch (err) {
      console.log(err);
      return undefined;
    }
  }
}

/**
 * ==============================
 *     Validator Terms Timing
 * ==============================
 */

export interface ValTermsTimingInterface {
  roundsSetup: bigint;
  roundsConfirm: bigint;
  roundsDurationMin: bigint;
  roundsDurationMax: bigint;
  roundMaxEnd: bigint;
}

export type ValTermsTimingArray = [bigint, bigint, bigint, bigint, bigint];

export class ValTermsTiming implements ValTermsTimingInterface {
  roundsSetup: bigint;
  roundsConfirm: bigint;
  roundsDurationMin: bigint;
  roundsDurationMax: bigint;
  roundMaxEnd: bigint;

  static readonly abi = new ABITupleType([
    new ABIUintType(64), //Rounds Setup
    new ABIUintType(64), //Rounds Confirm
    new ABIUintType(64), //Rounds Duration Min
    new ABIUintType(64), //Rounds Duration Max
    new ABIUintType(64), //Round Max End
  ]);

  constructor({
    roundsSetup,
    roundsConfirm,
    roundsDurationMin,
    roundsDurationMax,
    roundMaxEnd,
  }: ValTermsTimingInterface) {
    this.roundsSetup = roundsSetup;
    this.roundsConfirm = roundsConfirm;
    this.roundsDurationMin = roundsDurationMin;
    this.roundsDurationMax = roundsDurationMax;
    this.roundMaxEnd = roundMaxEnd;
  }

  static decodeBytes(data: Uint8Array): ValTermsTiming {
    const d = this.abi.decode(data) as ValTermsTimingArray;
    return new ValTermsTiming({
      roundsSetup: d[0],
      roundsConfirm: d[1],
      roundsDurationMin: d[2],
      roundsDurationMax: d[3],
      roundMaxEnd: d[4],
    });
  }

  static encodeArray({
    roundsSetup,
    roundsConfirm,
    roundsDurationMin,
    roundsDurationMax,
    roundMaxEnd,
  }: ValTermsTiming | ValTermsTimingInterface): ValTermsTimingArray {
    return [roundsSetup, roundsConfirm, roundsDurationMin, roundsDurationMax, roundMaxEnd];
  }
}

/**
 * ==============================
 *     Validator Terms Pricing
 * ==============================
 */

export interface ValTermsPricingInterface {
  commission: bigint;
  feeRoundMin: bigint;
  feeRoundVar: bigint;
  feeSetup: bigint;
  feeAssetId: bigint;
}

export type ValTermsPricingArray = [bigint, bigint, bigint, bigint, bigint];

export class ValTermsPricing implements ValTermsPricingInterface {
  commission: bigint;
  feeRoundMin: bigint;
  feeRoundVar: bigint;
  feeSetup: bigint;
  feeAssetId: bigint;

  static readonly abi = new ABITupleType([
    new ABIUintType(64), //Rounds Setup
    new ABIUintType(64), //Rounds Confirm
    new ABIUintType(64), //Rounds Duration Min
    new ABIUintType(64), //Rounds Duration Max
    new ABIUintType(64), //Round Max End
  ]);

  constructor({ commission, feeAssetId, feeRoundMin, feeRoundVar, feeSetup }: ValTermsPricingInterface) {
    this.commission = commission;
    this.feeRoundMin = feeRoundMin;
    this.feeSetup = feeSetup;
    this.feeRoundVar = feeRoundVar;
    this.feeAssetId = feeAssetId;
  }

  static decodeBytes(data: Uint8Array): ValTermsPricing {
    const d = this.abi.decode(data) as ValTermsPricingArray;
    return new ValTermsPricing({
      commission: d[0],
      feeRoundMin: d[1],
      feeRoundVar: d[2],
      feeSetup: d[3],
      feeAssetId: d[4],
    });
  }

  static encodeArray({
    commission,
    feeRoundMin,
    feeRoundVar,
    feeSetup,
    feeAssetId,
  }: ValTermsPricing | ValTermsPricingInterface): ValTermsPricingArray {
    return [commission, feeRoundMin, feeRoundVar, feeSetup, feeAssetId];
  }
}

/**
 * =====================================
 *     Validator Terms Staking Limits
 * =====================================
 */

export interface ValTermsStakeLimitsInterface {
  stakeMax: bigint;
  stakeGratis: bigint;
}

export type ValTermsStakeLimitsArray = [bigint, bigint];

export class ValTermsStakeLimits implements ValTermsStakeLimitsInterface {
  stakeMax: bigint;
  stakeGratis: bigint;

  constructor({ stakeMax, stakeGratis }: ValTermsStakeLimitsInterface) {
    this.stakeMax = stakeMax;
    this.stakeGratis = stakeGratis;
  }

  static readonly abi = new ABITupleType([
    new ABIUintType(64), //StakeMax
    new ABIUintType(64), //StakeGratis
  ]);

  static decodeBytes(data: Uint8Array): ValTermsStakeLimits {
    const d = this.abi.decode(data) as ValTermsStakeLimitsArray;

    return new ValTermsStakeLimits({
      stakeMax: d[0],
      stakeGratis: d[1],
    });
  }

  static encodeArray({
    stakeMax,
    stakeGratis,
  }: ValTermsStakeLimits | ValTermsStakeLimitsInterface): ValTermsStakeLimitsArray {
    return [stakeMax, stakeGratis];
  }
}

/**
 * =====================================
 *     Validator Terms Gating
 * =====================================
 */
export interface ValTermsGatingInterface {
  gatingAsaList: [[bigint, bigint], [bigint, bigint]];
}

export type ValTermsGatingArray = [[[bigint, bigint], [bigint, bigint]]];

export class ValTermsGating implements ValTermsGatingInterface {
  gatingAsaList: [[bigint, bigint], [bigint, bigint]];

  static readonly abi = new ABITupleType([new ABIArrayStaticType(new ABIArrayStaticType(new ABIUintType(64), 2), 2)]);

  constructor({ gatingAsaList }: ValTermsGatingInterface) {
    this.gatingAsaList = gatingAsaList;
  }

  static decodeBytes(data: Uint8Array) {
    const d = this.abi.decode(data) as ValTermsGatingArray;

    return new ValTermsGating({
      gatingAsaList: d[0],
    });
  }

  static encodeArray(data: ValTermsGating): ValTermsGatingArray {
    const { gatingAsaList } = data;
    return [gatingAsaList];
  }
}

/**
 * =====================================
 *     Validator Terms Warnings
 * =====================================
 */

export interface ValTermsWarningsInterface {
  cntWarningMax: bigint;
  roundsWarning: bigint;
}

export type ValTermsWarningsArray = [bigint, bigint];

export class ValTermsWarnings implements ValTermsWarningsInterface {
  cntWarningMax: bigint;
  roundsWarning: bigint;

  static readonly abi = new ABITupleType([
    new ABIUintType(64), //cnt_warning_max
    new ABIUintType(64), //rounds_warning
  ]);

  constructor({ cntWarningMax, roundsWarning }: ValTermsWarningsInterface) {
    this.cntWarningMax = cntWarningMax;
    this.roundsWarning = roundsWarning;
  }

  static decodeBytes(data: Uint8Array): ValTermsWarnings {
    const d = this.abi.decode(data) as ValTermsWarningsArray;
    return new ValTermsWarnings({
      cntWarningMax: d[0],
      roundsWarning: d[1],
    });
  }

  static encodeArray(data: ValTermsWarnings): ValTermsWarningsArray {
    const { cntWarningMax, roundsWarning } = data;
    return [cntWarningMax, roundsWarning];
  }
}

/**
 * =====================================
 *     Validator Self Disclosure
 * =====================================
 */

export interface ValSelfDisclosureInterface {
  name: string;
  https: string;
  countryCode: string;
  hwCat: bigint;
  nodeVersion: string;
}

export type ValSelfDisclosureArray = [Uint8Array, Uint8Array, Uint8Array, bigint, Uint8Array];

export class ValSelfDisclosure implements ValSelfDisclosureInterface {
  name: string;
  https: string;
  countryCode: string;
  hwCat: bigint;
  nodeVersion: string;

  static readonly abi = new ABITupleType([
    new ABIArrayStaticType(new ABIByteType(), 30), // name
    new ABIArrayStaticType(new ABIByteType(), 60), // https
    new ABIArrayStaticType(new ABIByteType(), 2), // countryCode
    new ABIUintType(64), // hwCat
    new ABIArrayStaticType(new ABIByteType(), 20), // nodeVersion
  ]);

  constructor({ name, https, countryCode, hwCat, nodeVersion }: ValSelfDisclosureInterface) {
    this.name = name;
    this.https = https;
    this.countryCode = countryCode;
    this.hwCat = hwCat;
    this.nodeVersion = nodeVersion;
  }

  static decodeBytes(data: Uint8Array) {
    const d = this.abi.decode(data) as ValSelfDisclosureArray;

    return new ValSelfDisclosure({
      name: bytesToStr(new Uint8Array(d[0])),
      https: bytesToStr(new Uint8Array(d[1])),
      countryCode: bytesToStr(new Uint8Array(d[2])),
      hwCat: d[3],
      nodeVersion: bytesToStr(new Uint8Array(d[4])),
    });
  }

  static encodeArray(data: ValSelfDisclosure): ValSelfDisclosureArray {
    const { name, https, countryCode, hwCat, nodeVersion } = data;

    return [strToBytes(name), strToBytes(https), strToBytes(countryCode), hwCat, strToBytes(nodeVersion)];
  }
}

/**
 * =====================================
 *     Del App List
 * =====================================
 */

export class DelAppList {
  static abi = new ABIArrayStaticType(new ABIUintType(64), 14);
  static decodeBytes(data: Uint8Array) {
    return this.abi.decode(data) as [
      bigint,
      bigint,
      bigint,
      bigint,
      bigint,
      bigint,
      bigint,
      bigint,
      bigint,
      bigint,
      bigint,
      bigint,
      bigint,
      bigint,
    ];
  }
}
