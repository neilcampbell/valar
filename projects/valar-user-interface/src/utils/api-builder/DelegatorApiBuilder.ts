import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { NoticeboardGlobalState } from "@/interfaces/contracts/Noticeboard";
import { PartnerInfo } from "@/interfaces/contracts/Partners";
import { UserInfo } from "@/interfaces/contracts/User";
import {
  ValAdGlobalStateInterface,
  ValidatorAdGlobalState,
} from "@/interfaces/contracts/ValidatorAd";
import { noticeboardAppID } from "@/constants/platform";
import { AlgorandClient, microAlgos } from "@algorandfoundation/algokit-utils";
import { BoxReference } from "@algorandfoundation/algokit-utils/types/app";
import {
  ABIAddressType,
  bigIntToBytes,
  getApplicationAddress,
  makeKeyRegistrationTxnWithSuggestedParamsFromObject,
  Transaction,
  TransactionSigner,
} from "algosdk";

import { BoxUtils } from "../contract/box-utils";
import {
  calculateFeeRound,
  calculateFeesPartner,
  calculateOperationalFee,
} from "../contract/helpers";
import { TxnParams } from "../txn-params";
import { KeyRegParams } from "@/lib/types";
import { bytesToStr } from "../convert";
import { ParamsCache } from "../paramsCache";
import { User } from "@/store/userStore";
import { ASA_ID_ALGO, FEE_OPT_IN_PERFORMANCE_TRACKING, MBR_USER_BOX, MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE, ZERO_ADDRESS } from "@/constants/smart-contracts";
import { BOX_ASA_KEY_PREFIX, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY, BOX_PARTNERS_PREFIX, BOX_SIZE_PER_REF } from "@/constants/smart-contracts";

export class DelegatorApiBuilder {
  /**
   * ================================
   *          Contract Create
   * ================================
   */

  static async contractCreate({
    algorandClient,
    gsNoticeBoard,
    gsValidatorAd,
    userAddress,
    partner,
    delUserInfo,
    stakeMax,
    roundsDuration,
    delBeneficiary,
    signer,
  }: {
    algorandClient: AlgorandClient;
    gsNoticeBoard: NoticeboardGlobalState;
    gsValidatorAd: ValAdGlobalStateInterface;
    userAddress: string;
    partner?: PartnerInfo;
    delUserInfo: UserInfo;
    stakeMax: bigint;
    roundsDuration: bigint;
    delBeneficiary: string;
    signer: TransactionSigner;
  }) {

    const valAssetId = gsValidatorAd.termsPrice.feeAssetId;
    const valAppId = gsValidatorAd.appId;

    //Foreign Assets
    const foreignAssets = gsValidatorAd.termsReqs.gatingAsaList
      .filter((asaReg) => asaReg[0] != ASA_ID_ALGO)
      .map((asaReg) => Number(asaReg[0]));
    if (valAssetId != ASA_ID_ALGO) {
      foreignAssets.push( Number(valAssetId) );
    }

    //Foreign Accounts
    const foreignAccounts = [delBeneficiary]

    const foreignApps = [Number(valAppId)];

    const noticeboardAddress = getApplicationAddress(noticeboardAppID);

    const valOwner = gsValidatorAd.valOwner;

    const tcSha256 = gsNoticeBoard.tcSha256;

    //MBR Calculation
    const mbrAmount =
      Number(gsNoticeBoard.noticeboardFees.delContractCreation) +
      MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE;

    const mbrTxn = await algorandClient.transactions.payment({
      sender: userAddress,
      receiver: noticeboardAddress,
      amount: microAlgos(mbrAmount),
      signer,
    });

    //Fee Amount Calculation
    const feeRound = calculateFeeRound(
      stakeMax,
      gsValidatorAd.termsPrice.feeRoundMin,
      gsValidatorAd.termsPrice.feeRoundVar,
    );
    const feeSetup = gsValidatorAd.termsPrice.feeSetup;

    let partnerAmount = 0n;
    let partnerAddress = ZERO_ADDRESS;
    if(partner){
      partnerAddress = partner.address;
      const partnerCommission = partner.partnerCommission;
      const [feeSetupPartner, feeRoundPartner] = calculateFeesPartner(partnerCommission, feeSetup, feeRound);
      partnerAmount = feeSetupPartner + calculateOperationalFee(feeRoundPartner, roundsDuration, 0n);
    }

    const feeAmount = feeSetup + calculateOperationalFee(feeRound, roundsDuration, 0n) + partnerAmount;

    let feeTxn: Transaction;
    if (valAssetId != ASA_ID_ALGO) {
      feeTxn = await algorandClient.transactions.assetTransfer({
        assetId: valAssetId,
        sender: userAddress,
        receiver: noticeboardAddress,
        amount: BigInt(feeAmount),
        signer,
      });
    } else {
      feeTxn = await algorandClient.transactions.payment({
        sender: userAddress,
        receiver: noticeboardAddress,
        amount: microAlgos(Number(feeAmount)),
        signer,
      });
    }

    //BoxesDel
    const boxDel = (
      await BoxUtils.getAppBox(
        algorandClient.client.algod,
        Number(valAppId),
        BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
      )
    ).value;
    const boxDelSize = boxDel.length;
    const numLoadVal = Math.ceil(boxDelSize / BOX_SIZE_PER_REF);
    const boxesDel_ValAd = BoxUtils.createBoxesWithLength(
      Number(valAppId),
      BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
      numLoadVal,
    );

    //Boxes Config
    const boxesUser = BoxUtils.createBoxes(0, [userAddress]);
    const boxesOwner = BoxUtils.createBoxes(0, [valOwner]);
    const boxesPartner: BoxReference[] = [
      {
        appId: 0,
        name: new Uint8Array([
          ...BOX_PARTNERS_PREFIX,
          ...new ABIAddressType().encode(partnerAddress),
        ]),
      },
    ];

    // Get validator owner user info
    const valUserInfo = await UserInfo.getUserInfo(algorandClient.client.algod, valOwner);
    const valAppIdx = valUserInfo!.getAppIndex(valAppId);
    const delAppIdx = delUserInfo.getFreeAppIndex();

    const txnParams = await TxnParams.setTxnFees(10, true);

    return {
      tcSha256,
      foreignApps,
      foreignAssets,
      foreignAccounts,
      valAppId,
      valAppIdx,
      delAppIdx,
      valOwner,
      partnerAddress,
      boxesDel_ValAd,
      boxesContractCreate: [...boxesUser, ...boxesOwner, ...boxesPartner],
      txnParams,
      mbrTxn,
      feeTxn,
    };
  }

  /**
   * ================================
   *         Contract Claim
   * ================================
   */

  static async contractClaim({
    gsValidatorAd,
    gsDelContract,
    valUserInfo,
    delUserInfo,
    valAppId,
    delAppId,
  }: {
    gsValidatorAd: ValidatorAdGlobalState;
    gsDelContract: DelegatorContractGlobalState;
    valUserInfo: UserInfo;
    delUserInfo: UserInfo;
    valAppId: bigint;
    delAppId: bigint;
  }) {
    const delManager = gsDelContract.delManager;
    const valOwner = gsValidatorAd.valOwner;

    const boxesDelManager = BoxUtils.createBoxes(0, [delManager]);
    const boxesValOwner = BoxUtils.createBoxes(0, [valOwner]);

    const valAppIdx = valUserInfo.getAppIndex(valAppId);
    const delAppIdx = delUserInfo.getFreeAppIndex();

    const assetId = gsDelContract.delegationTermsGeneral.feeAssetId;

    let foreignAssets: number[] = [];
    let boxesAsset: BoxReference[] = [];

    if (assetId != ASA_ID_ALGO) {
      foreignAssets = [Number(assetId)];
      boxesAsset = [
        {
          appId: valAppId,
          name: new Uint8Array([
            ...BOX_ASA_KEY_PREFIX,
            ...bigIntToBytes(assetId, 8),
          ]),
        },
      ];
    }

    const partnerAddress = gsDelContract.delegationTermsGeneral.partnerAddress;
    const foreignAccounts = [partnerAddress, delManager];

    const txnParams = await TxnParams.setTxnFees(6, true);

    return {
      delAppId,
      valAppId,
      delAppIdx,
      valAppIdx,
      delManager,
      valOwner,
      boxesContractClaim: [...boxesValOwner, ...boxesDelManager, ...boxesAsset],
      foreignAccounts,
      foreignAssets,
      txnParams,
    };
  }

  /**
   * ================================
   *         Contract Delete
   * ================================
   */

  static async contractDelete({
    algorandClient,
    gsDelCo,
    gsValAd,
    userAddress,
    delUserInfo,
  }: {
    algorandClient: AlgorandClient;
    gsDelCo: DelegatorContractGlobalState;
    gsValAd: ValidatorAdGlobalState;
    userAddress: string;
    delUserInfo: UserInfo;
  }) {
    const valAppId = gsDelCo.validatorAdAppId;
    const delAppId = gsDelCo.appId;

    const assetId = gsDelCo.delegationTermsGeneral.feeAssetId;

    let foreignAssets: number[] = [];
    if (assetId != ASA_ID_ALGO) {
      foreignAssets = [Number(assetId)];
    }

    const valOwner = gsValAd.valOwner;
    const delManager = userAddress;
    const boxesDelManager = BoxUtils.createBoxes(0, [delManager]);
    const boxesValOwner = BoxUtils.createBoxes(0, [valOwner]);

    // Get validator owner user info
    const valUserInfo = await UserInfo.getUserInfo(algorandClient.client.algod, valOwner);
    const valAppIdx = valUserInfo!.getAppIndex(valAppId);
    const delAppIdx = delUserInfo.getAppIndex(delAppId);

    const txnParams = await TxnParams.setTxnFees(6, true);

    return {
      delAppId,
      valAppId,
      delAppIdx,
      valAppIdx,
      valOwner,
      foreignAssets,
      boxesContractDelete: [...boxesValOwner, ...boxesDelManager],
      txnParams,
    };
  }

  /**
   * ================================
   *       Contract  Withdraw
   * ================================
   */

  static async contractWithdraw({
    algorandClient,
    gsDelCo,
    gsValAd,
    userAddress,
    delUserInfo,
    delKeyRegParams,
  }: {
    algorandClient: AlgorandClient;
    gsDelCo: DelegatorContractGlobalState;
    gsValAd: ValidatorAdGlobalState;
    userAddress: string;
    delUserInfo: UserInfo;
    delKeyRegParams: KeyRegParams | undefined;
  }) {
    const valAppId = gsDelCo.validatorAdAppId;
    const delAppId = gsDelCo.appId;

    const valOwner = gsValAd.valOwner;

    const delManager = userAddress;
    const boxesDelManager = BoxUtils.createBoxes(0, [delManager]);
    const boxesValOwner = BoxUtils.createBoxes(0, [valOwner]);

    // Get validator owner user info
    const valUserInfo = await UserInfo.getUserInfo(algorandClient.client.algod, valOwner);
    const valAppIdx = valUserInfo!.getAppIndex(valAppId);
    const delAppIdx = delUserInfo.getAppIndex(delAppId);

    const assetId = gsDelCo.delegationTermsGeneral.feeAssetId;

    let foreignAssets: number[] = [];
    let boxesAsset: BoxReference[] = [];

    if (assetId != ASA_ID_ALGO) {
      foreignAssets = [Number(assetId)];
      boxesAsset = [
        {
          appId: Number(valAppId),
          name: new Uint8Array([
            ...BOX_ASA_KEY_PREFIX,
            ...bigIntToBytes(assetId, 8),
          ]),
        },
      ];
    }

    const partnerAddress = gsDelCo.delegationTermsGeneral.partnerAddress;
    const foreignAccounts = [partnerAddress];

    const txnParams = await TxnParams.setTxnFees(6, true);

    let txnKeyDeReg = undefined;
    if(delKeyRegParams && (bytesToStr(gsDelCo.voteKey) === bytesToStr(delKeyRegParams.voteKey))){
      // Create key deregistration transaction if keys are still active
      txnKeyDeReg = makeKeyRegistrationTxnWithSuggestedParamsFromObject({
        from: userAddress,
        suggestedParams: await ParamsCache.getSuggestedParams(),
      });
    }

    return {
      delAppId,
      valAppId,
      delAppIdx,
      valAppIdx,
      valOwner,
      foreignAssets,
      foreignAccounts,
      txnKeyDeReg,
      boxesContractWithdraw: [
        ...boxesDelManager,
        ...boxesValOwner,
        ...boxesAsset,
      ],
      txnParams,
    };
  }

  /**
   * ================================
   *          Keys Confirm
   * ================================
   */

  static async keysConfirm({
    algorandClient,
    gsValAd,
    gsDelCo,
    userAddress,
    user,
    signer,
  }: {
    algorandClient: AlgorandClient;
    gsValAd: ValidatorAdGlobalState;
    gsDelCo: DelegatorContractGlobalState;
    userAddress: string;
    user: User;
    signer: TransactionSigner;
  }) {
    const valAppId = gsDelCo.validatorAdAppId;
    const delAppId = gsDelCo.appId;

    const valOwner = gsValAd.valOwner;
    const delManager = userAddress;
    const boxesDelManager = BoxUtils.createBoxes(0, [delManager]);
    const boxesValOwner = BoxUtils.createBoxes(0, [valOwner]);

    // Get validator owner user info
    const valUserInfo = await UserInfo.getUserInfo(algorandClient.client.algod, valOwner);
    const valAppIdx = valUserInfo!.getAppIndex(valAppId);
    const delAppIdx = user.userInfo!.getAppIndex(delAppId);

    let keyRegFee = FEE_OPT_IN_PERFORMANCE_TRACKING;
    let addedTxn = 0;
    if(user.trackedPerformance){
      keyRegFee = 0;
      addedTxn = 1;
    }

    const txnParams = await TxnParams.setTxnFees(3 + addedTxn, true);

    const txnKeyReg = await algorandClient.transactions.onlineKeyRegistration({
      sender: gsDelCo.delBeneficiary,
      voteKey: gsDelCo.voteKey,
      selectionKey: gsDelCo.selKey,
      voteFirst: gsDelCo.roundStart,
      voteLast: gsDelCo.roundEnd,
      voteKeyDilution: gsDelCo.voteKeyDilution,
      stateProofKey: gsDelCo.stateProofKey,
      staticFee: microAlgos(keyRegFee),
      signer,
    });

    return {
      delAppId,
      valAppId,
      delAppIdx,
      valAppIdx,
      valOwner,
      txnKeyReg,
      boxesKeysConfirm: [...boxesValOwner, ...boxesDelManager],
      txnParams,
    };
  }

  /**
   * ================================
   *  User Create and Contract Create
   * ================================
   */

  static async userCreateAndContractCreate({
    algorandClient,
    gsNoticeBoard,
    gsValidatorAd,
    userAddress,
    partner,
    stakeMax,
    roundsDuration,
    delBeneficiary,
    signer,
  }: {
    algorandClient: AlgorandClient;
    gsNoticeBoard: NoticeboardGlobalState;
    gsValidatorAd: ValAdGlobalStateInterface;
    userAddress: string;
    partner?: PartnerInfo;
    stakeMax: bigint;
    roundsDuration: bigint;
    delBeneficiary: string;
    signer: TransactionSigner;
  }) {
    // UserCreate-related:
    const userRegFees = Number(gsNoticeBoard!.noticeboardFees.delUserReg);

    const amountUserCreate: number = MBR_USER_BOX + userRegFees;
    const noticeboardAddress = getApplicationAddress(noticeboardAppID);

    //MBR Increase
    const feeTxnUserCreate = await algorandClient.transactions.payment({
      sender: userAddress,
      receiver: noticeboardAddress,
      amount: microAlgos(amountUserCreate),
      signer,
    });

    //Getting Last User
    const userLast = gsNoticeBoard.dllDel.userLast;

    const boxesUserCreate: BoxReference[] = BoxUtils.createBoxes(0, [userAddress, userLast]);

    // ContractCreate-related:
    const valAssetId = gsValidatorAd.termsPrice.feeAssetId;
    const valAppId = gsValidatorAd.appId;

    //Foreign Assets
    const foreignAssets = gsValidatorAd.termsReqs.gatingAsaList
      .filter((asaReg) => asaReg[0] != ASA_ID_ALGO)
      .map((asaReg) => Number(asaReg[0]));
    if (valAssetId != ASA_ID_ALGO) {
      foreignAssets.push( Number(valAssetId) );
    }

    //Foreign Accounts
    const foreignAccounts = [delBeneficiary]

    const foreignApps = [Number(valAppId)];

    const valOwner = gsValidatorAd.valOwner;

    const tcSha256 = gsNoticeBoard.tcSha256;

    //MBR Calculation
    const mbrAmount =
      Number(gsNoticeBoard.noticeboardFees.delContractCreation) +
      MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE;

    const mbrTxn = await algorandClient.transactions.payment({
      sender: userAddress,
      receiver: noticeboardAddress,
      amount: microAlgos(mbrAmount),
      signer,
    });

    //Fee Amount Calculation
    const feeRound = calculateFeeRound(
      stakeMax,
      gsValidatorAd.termsPrice.feeRoundMin,
      gsValidatorAd.termsPrice.feeRoundVar,
    );
    const feeSetup = gsValidatorAd.termsPrice.feeSetup;

    let partnerAmount = 0n;
    let partnerAddress = ZERO_ADDRESS;
    if(partner){
      partnerAddress = partner.address;
      const partnerCommission = partner.partnerCommission;
      const [feeSetupPartner, feeRoundPartner] = calculateFeesPartner(partnerCommission, feeSetup, feeRound);
      partnerAmount = feeSetupPartner + calculateOperationalFee(feeRoundPartner, roundsDuration, 0n);
    }

    const feeAmount = feeSetup + calculateOperationalFee(feeRound, roundsDuration, 0n) + partnerAmount;

    let feeTxn: Transaction;
    if (valAssetId != ASA_ID_ALGO) {
      feeTxn = await algorandClient.transactions.assetTransfer({
        assetId: valAssetId,
        sender: userAddress,
        receiver: noticeboardAddress,
        amount: BigInt(feeAmount),
        signer,
      });
    } else {
      feeTxn = await algorandClient.transactions.payment({
        sender: userAddress,
        receiver: noticeboardAddress,
        amount: microAlgos(Number(feeAmount)),
        signer,
      });
    }

    //BoxesDel
    const boxDel = (
      await BoxUtils.getAppBox(
        algorandClient.client.algod,
        Number(valAppId),
        BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
      )
    ).value;
    const boxDelSize = boxDel.length;
    const numLoadVal = Math.ceil(boxDelSize / BOX_SIZE_PER_REF);
    const boxesDel_ValAd = BoxUtils.createBoxesWithLength(
      Number(valAppId),
      BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
      numLoadVal,
    );

    //Boxes Config
    const boxesOwner = BoxUtils.createBoxes(0, [valOwner]);
    const boxesPartner: BoxReference[] = [
      {
        appId: 0,
        name: new Uint8Array([
          ...BOX_PARTNERS_PREFIX,
          ...new ABIAddressType().encode(partnerAddress),
        ]),
      },
    ];

    // Get validator owner user info
    const valUserInfo = await UserInfo.getUserInfo(algorandClient.client.algod, valOwner);
    const valAppIdx = valUserInfo!.getAppIndex(valAppId);
    const delAppIdx = 0n;  // First contract because new user

    const txnParams = await TxnParams.setTxnFees(10+1, true);

    return {
      tcSha256,
      foreignApps,
      foreignAssets,
      foreignAccounts,
      valAppId,
      valAppIdx,
      delAppIdx,
      valOwner,
      partnerAddress,
      feeTxnUserCreate,
      boxesUserCreate,
      boxesDel_ValAd,
      boxesContractCreate: [...boxesOwner, ...boxesPartner],
      txnParams,
      mbrTxn,
      feeTxn,
    };
  }

}
