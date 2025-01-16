import { BoxExistsResponse, BoxUtils } from "@/utils/contract/box-utils";
import {
  ABIAddressType,
  ABIArrayStaticType,
  ABIByteType,
  ABITupleType,
  ABIUintType,
} from "algosdk";
import AlgodClient from "algosdk/dist/types/client/v2/algod/algod";

/**
 * ===============================
 *     User Info
 * ===============================
 */

export interface UserInfoInterface {
  role: Uint8Array;
  dllName: Uint8Array;

  prevUser: string;
  nextUser: string;

  appIds: bigint[];
  cntAppIds: bigint;
}

export type UserInfoArray = [
  Uint8Array,
  Uint8Array,
  string,
  string,
  bigint[],
  bigint,
];

export class UserInfo implements UserInfoInterface {
  role: Uint8Array;
  dllName: Uint8Array;

  prevUser: string;
  nextUser: string;

  appIds: bigint[];
  cntAppIds: bigint;

  static readonly abi = new ABITupleType([
    new ABIArrayStaticType(new ABIByteType(), 4), //Role
    new ABIArrayStaticType(new ABIByteType(), 8), // DLL Name
    new ABIAddressType(), //Prev User
    new ABIAddressType(), //Next User
    new ABIArrayStaticType(new ABIUintType(64), 110), //App Ids
    new ABIUintType(64), //CntAppIds
  ]);

  constructor({
    role,
    dllName,
    prevUser,
    nextUser,
    appIds,
    cntAppIds,
  }: UserInfoInterface) {
    this.role = role;
    this.dllName = dllName;
    this.prevUser = prevUser;
    this.nextUser = nextUser;
    this.appIds = appIds;
    this.cntAppIds = cntAppIds;
  }

  static fromBytes(data: Uint8Array) {
    const d = this.abi.decode(data) as UserInfoArray;

    return new UserInfo({
      role: d[0],
      dllName: d[1],
      prevUser: d[2],
      nextUser: d[3],
      appIds: d[4],
      cntAppIds: d[5],
    });
  }

  getFreeAppIndex() {
    return this.getAppIndex(0n);
  }

  getAppIndex(appId: bigint): number {
    try {
      const index = this.appIds.indexOf(appId);
      return index === -1 ? 0 : index;
    } catch (e) {
      return 0;
      //Returns 0 if not found
    }
  }

  static async getUserInfo(
    algodClient: AlgodClient,
    userAddress: string,
  ): Promise<UserInfo | undefined> {
    const boxRes: BoxExistsResponse = await BoxUtils.getNoticeboardBox(
      algodClient,
      new Uint8Array([...new ABIAddressType().encode(userAddress)]),
    );
    if (!boxRes.exists) return undefined;

    return UserInfo.fromBytes(boxRes.value);
  }
}
