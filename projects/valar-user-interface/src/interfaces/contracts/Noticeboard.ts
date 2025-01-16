import { NoticeboardClient } from "@/contracts/Noticeboard";
import { ABIAddressType, ABITupleType, ABIUintType } from "algosdk";

/**
 * ===============================
 *     Noticeboard Global State
 * ===============================
 */

export interface NBGlobalStateInterface {
  plaManager: string;

  tcSha256: Uint8Array;

  noticeboardFees: NBFees;
  noticeboardTermsTiming: NBTermsTiming;
  noticeboardTermsNode: NBTermsNodeLimits;

  state: Uint8Array;

  appIdOld: bigint;
  appIdNew: bigint;

  dllVal: UsersDoubleLinkedList;
  dllDel: UsersDoubleLinkedList;
}

export class NoticeboardGlobalState implements NBGlobalStateInterface {
  plaManager: string;

  tcSha256: Uint8Array;

  noticeboardFees: NBFees;
  noticeboardTermsTiming: NBTermsTiming;
  noticeboardTermsNode: NBTermsNodeLimits;

  state: Uint8Array;

  appIdOld: bigint;
  appIdNew: bigint;

  dllVal: UsersDoubleLinkedList;
  dllDel: UsersDoubleLinkedList;

  constructor({
    plaManager,
    tcSha256,
    noticeboardFees,
    noticeboardTermsTiming,
    noticeboardTermsNode,
    state,
    appIdOld,
    appIdNew,
    dllVal,
    dllDel,
  }: NBGlobalStateInterface) {
    this.plaManager = plaManager;
    this.tcSha256 = tcSha256;
    this.noticeboardFees = noticeboardFees;
    this.noticeboardTermsTiming = noticeboardTermsTiming;
    this.noticeboardTermsNode = noticeboardTermsNode;
    this.state = state;
    this.appIdOld = appIdOld;
    this.appIdNew = appIdNew;
    this.dllVal = dllVal;
    this.dllDel = dllDel;
  }

  // Fetches info from blockchain about noticeboard
  static async getGlobalState(
    noticeboardClient: NoticeboardClient,
  ): Promise<NoticeboardGlobalState | undefined> {
    try {
      const gs = await noticeboardClient.getGlobalState();

      return new NoticeboardGlobalState({
        plaManager: new ABIAddressType().decode(gs.plaManager!.asByteArray()),

        tcSha256: gs.tcSha256!.asByteArray(),

        noticeboardFees: NBFees.decodeBytes(gs.noticeboardFees!.asByteArray()),
        noticeboardTermsTiming: NBTermsTiming.decodeBytes(gs.noticeboardTermsTiming!.asByteArray()),
        noticeboardTermsNode: NBTermsNodeLimits.decodeBytes(gs.noticeboardTermsNode!.asByteArray()),

        state: gs.state!.asByteArray(),

        appIdNew: gs.appIdNew!.asBigInt(),
        appIdOld: gs.appIdOld!.asBigInt(),

        dllDel: UsersDoubleLinkedList.decodeBytes(gs.dllDel!.asByteArray()),
        dllVal: UsersDoubleLinkedList.decodeBytes(gs.dllVal!.asByteArray()),
      });
    } catch (err) {
      return undefined;
    }
  }
}

/**
 * ==============================
 *     Noticeboard Fees
 * ==============================
 */

export interface NBFeesInterface {
  commissionMin: bigint;
  valUserReg: bigint;
  delUserReg: bigint;
  valAdCreation: bigint;
  delContractCreation: bigint;
}

export type NBFeesArray = [bigint, bigint, bigint, bigint, bigint];

export class NBFees implements NBFeesInterface {
  commissionMin: bigint;
  valUserReg: bigint;
  delUserReg: bigint;
  valAdCreation: bigint;
  delContractCreation: bigint;

  static readonly abi = new ABITupleType([
    new ABIUintType(64), //Commission Min
    new ABIUintType(64), //ValUserReg
    new ABIUintType(64), //DelUserReg
    new ABIUintType(64), //ValAdCreation
    new ABIUintType(64), //DelContractCreation
  ]);

  constructor({
    commissionMin,
    valUserReg,
    delUserReg,
    valAdCreation,
    delContractCreation,
  }: NBFeesInterface) {
    this.commissionMin = commissionMin;
    this.valUserReg = valUserReg;
    this.delUserReg = delUserReg;
    this.valAdCreation = valAdCreation;
    this.delContractCreation = delContractCreation;
  }

  static decodeBytes(data: Uint8Array) {
    const d = this.abi.decode(data) as NBFeesArray;

    return new NBFees({
      commissionMin: d[0],
      valUserReg: d[1],
      delUserReg: d[2],
      valAdCreation: d[3],
      delContractCreation: d[4],
    });
  }
}

/**
 * ===============================
 *     Noticeboard Terms Timing
 * ===============================
 */

export interface NBTermsTimingInterface {
  roundsDurationMin: bigint;
  roundsDurationMax: bigint;
  beforeExpiry: bigint;
  reportPeriod: bigint;
}

export type NBTermsTimingArray = [bigint, bigint, bigint, bigint];

export class NBTermsTiming implements NBTermsTimingInterface {
  roundsDurationMin: bigint;
  roundsDurationMax: bigint;
  beforeExpiry: bigint;
  reportPeriod: bigint;

  static readonly abi = new ABITupleType([
    new ABIUintType(64), //Rounds Duration Min
    new ABIUintType(64), //Rounds Duration Max
    new ABIUintType(64), //Before Expiry
    new ABIUintType(64), //Report Period
  ]);

  constructor({
    roundsDurationMin,
    roundsDurationMax,
    beforeExpiry,
    reportPeriod,
  }: NBTermsTimingInterface) {
    this.roundsDurationMin = roundsDurationMin;
    this.roundsDurationMax = roundsDurationMax;
    this.beforeExpiry = beforeExpiry;
    this.reportPeriod = reportPeriod;
  }

  static decodeBytes(data: Uint8Array) {
    const d = this.abi.decode(data) as NBTermsTimingArray;

    return new NBTermsTiming({
      roundsDurationMin: d[0],
      roundsDurationMax: d[1],
      beforeExpiry: d[2],
      reportPeriod: d[3],
    });
  }
}

/**
 * =====================================
 *     Noticeboard Terms Node Limits
 * =====================================
 */

export interface NBTermsNodeLimitsInterface {
  stakeMaxMax: bigint;
  stakeMaxMin: bigint;
  cntDelMax: bigint;
}

export type NBTermsNodeLimitsArray = [bigint, bigint, bigint];

export class NBTermsNodeLimits implements NBTermsNodeLimitsInterface {
  stakeMaxMax: bigint;
  stakeMaxMin: bigint;
  cntDelMax: bigint;

  static readonly abi = new ABITupleType([
    new ABIUintType(64),
    new ABIUintType(64),
    new ABIUintType(64),
  ]);

  constructor({
    stakeMaxMax,
    stakeMaxMin,
    cntDelMax,
  }: NBTermsNodeLimitsInterface) {
    this.stakeMaxMax = stakeMaxMax;
    this.stakeMaxMin = stakeMaxMin;
    this.cntDelMax = cntDelMax;
  }

  static decodeBytes(data: Uint8Array) {
    const d = this.abi.decode(data) as NBTermsNodeLimitsArray;

    return new NBTermsNodeLimits({
      stakeMaxMax: d[0],
      stakeMaxMin: d[1],
      cntDelMax: d[2],
    });
  }
}

// /**
//  * ===============================
//  *     Noticeboard Terms Pricing
//  * ===============================
//  */

// export interface NBTermsPricingInterface {
//   commissionMin: bigint;
//   feeRoundMin: bigint;
//   feeRoundVarMin: bigint;
//   feeSetupMin: bigint;
// }

// export type NBTermsPricingArray = [bigint, bigint, bigint, bigint];

// export class NBTermsPricing implements NBTermsPricingInterface {
//   commissionMin: bigint;
//   feeRoundMin: bigint;
//   feeRoundVarMin: bigint;
//   feeSetupMin: bigint;

//   static readonly abi = new ABITupleType([
//     new ABIUintType(63), //ValUserReg
//     new ABIUintType(63), //DelUserReg
//     new ABIUintType(63), //ValAdCreation
//     new ABIUintType(63), //DelContractCreation
//   ]);

//   constructor({
//     commissionMin,
//     feeRoundMin,
//     feeRoundVarMin,
//     feeSetupMin,
//   }: NBTermsPricingInterface) {
//     this.commissionMin = commissionMin;
//     this.feeRoundMin = feeRoundMin;
//     this.feeRoundVarMin = feeRoundVarMin;
//     this.feeSetupMin = feeSetupMin;
//   }

//   static decodeBytes(data: Uint8Array) {
//     const d = this.abi.decode(data) as NBTermsPricingArray;

//     return new NBTermsPricing({
//       commissionMin: d[0],
//       feeRoundMin: d[1],
//       feeRoundVarMin: d[2],
//       feeSetupMin: d[3],
//     });
//   }
// }

// /**
//  * ===============================
//  *     Noticeboard Terms Stake
//  * ===============================
//  */

// export interface NBTermsStakeLimitsInterface {
//   stakeMax: bigint;
// }

// export class NBTermsStakeLimits implements NBTermsStakeLimitsInterface {
//   stakeMax: bigint;

//   static readonly abi = new ABITupleType([
//     new ABIUintType(64), //Stake Max
//   ]);

//   constructor({ stakeMax }: NBTermsStakeLimitsInterface) {
//     this.stakeMax = stakeMax;
//   }

//   static decodeBytes(data: Uint8Array) {
//     const d = this.abi.decode(data) as [bigint];

//     return new NBTermsStakeLimits({
//       stakeMax: d[0],
//     });
//   }
// }

// /**
//  * ===============================
//  *     Noticeboard Terms Deposits
//  * ===============================
//  */

// export interface NBTermsDepositsInterface {
//   depositsMinMin: [bigint, bigint];
//   depositsVarMin: [bigint, bigint];
//   depositsMinMax: [bigint, bigint];
//   depositsVarMax: [bigint, bigint];
//   checkApp: bigint;
//   checkAppFinal: bigint;
// }

// export type NBTermsDepositsArray = [
//   [bigint, bigint],
//   [bigint, bigint],
//   [bigint, bigint],
//   [bigint, bigint],
//   bigint,
//   bigint,
// ];

// export class NBTermsDeposits implements NBTermsDepositsInterface {
//   depositsMinMin: [bigint, bigint];
//   depositsVarMin: [bigint, bigint];
//   depositsMinMax: [bigint, bigint];
//   depositsVarMax: [bigint, bigint];
//   checkApp: bigint;
//   checkAppFinal: bigint;

//   static readonly abi = new ABITupleType([
//     new ABITupleType([new ABIUintType(64), new ABIUintType(64)]), //deposits_min_min
//     new ABITupleType([new ABIUintType(64), new ABIUintType(64)]), //deposits_var_min
//     new ABITupleType([new ABIUintType(64), new ABIUintType(64)]), //deposits_min_max
//     new ABITupleType([new ABIUintType(64), new ABIUintType(64)]), //deposits_var_max
//     new ABIUintType(64), //check_app
//     new ABIUintType(64), //check_app_final
//   ]);

//   constructor({
//     depositsMinMin,
//     depositsVarMin,
//     depositsMinMax,
//     depositsVarMax,
//     checkApp,
//     checkAppFinal,
//   }: NBTermsDepositsInterface) {
//     this.depositsMinMin = depositsMinMin;
//     this.depositsVarMin = depositsVarMin;
//     this.depositsMinMax = depositsMinMax;
//     this.depositsVarMax = depositsVarMax;
//     this.checkApp = checkApp;
//     this.checkAppFinal = checkAppFinal;
//   }

//   static decodeBytes(data: Uint8Array) {
//     const d = this.abi.decode(data) as NBTermsDepositsArray;

//     return new NBTermsDeposits({
//       depositsMinMin: d[0],
//       depositsVarMin: d[1],
//       depositsMinMax: d[2],
//       depositsVarMax: d[3],
//       checkApp: d[4],
//       checkAppFinal: d[5],
//     });
//   }
// }

/**
 * ===============================
 *     User DoubleLinkedList
 * ===============================
 */

export interface UsersDoubleLinkedListInterface {
  cntUsers: bigint;
  userFirst: string;
  userLast: string;
}

export type UsersDoubleLinkedListArray = [bigint, string, string];

export class UsersDoubleLinkedList implements UsersDoubleLinkedListInterface {
  cntUsers: bigint;
  userFirst: string;
  userLast: string;

  static readonly abi = new ABITupleType([
    new ABIUintType(64), // cntUsers
    new ABIAddressType(), // userFirst
    new ABIAddressType(), // userLast
  ]);

  constructor({
    cntUsers,
    userFirst,
    userLast,
  }: UsersDoubleLinkedListInterface) {
    this.cntUsers = cntUsers;
    this.userFirst = userFirst;
    this.userLast = userLast;
  }

  static decodeBytes(data: Uint8Array) {
    const d = this.abi.decode(data) as UsersDoubleLinkedListArray;

    return new UsersDoubleLinkedList({
      cntUsers: d[0],
      userFirst: d[1],
      userLast: d[2],
    });
  }
}
