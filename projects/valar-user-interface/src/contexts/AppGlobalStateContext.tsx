import { fetchAllVal } from "@/api/queries/user";
import { fetchValidatorAds } from "@/api/queries/validator-ads";
import { NoticeboardClient } from "@/contracts/Noticeboard";
import { NoticeboardApp } from "@/interfaces/client/NoticeboardApp";
import { NoticeboardGlobalState } from "@/interfaces/contracts/Noticeboard";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { StakingData } from "@/lib/types";
import { noticeboardAppID } from "@/constants/platform";
import { estimateAPY } from "@/utils/convert";
import { getAlgodConfigFromViteEnvironment } from "@/utils/config/getAlgoClientConfigs";
import { ParamsCache } from "@/utils/paramsCache";
import { AlgorandClient } from "@algorandfoundation/algokit-utils";
import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";

/**
 * ===============================
 *        Client Config
 * ===============================
 */

const algodConfig = getAlgodConfigFromViteEnvironment();
const defaultAlgorandClient: AlgorandClient = AlgorandClient.fromConfig({
  algodConfig,
});

const defaultNoticeboardClient: NoticeboardClient = new NoticeboardClient(
  {
    resolveBy: "id",
    id: noticeboardAppID,
  },
  defaultAlgorandClient.client.algod,
);

const defaultNoticeboardApp: NoticeboardApp = {
  appId: noticeboardAppID,
  client: defaultNoticeboardClient,
  globalState: undefined,
};

let apiStakingDataSource = "";
if(import.meta.env.VITE_ENVIRONMENT === "local"){
  apiStakingDataSource = "/api";
} else {
  apiStakingDataSource = import.meta.env.VITE_ALGORAND_STATS;
}

/**
 * ========================
 *     App Global Context
 * ========================
 */

const AppGlobalStateContext = createContext<
  | {
      noticeboardApp: NoticeboardApp;
      algorandClient: AlgorandClient;
      valAdsMap: Map<bigint, ValidatorAdGlobalState> | undefined;
      valsMap: Map<string, bigint[]> | undefined;
      stakingData: StakingData | undefined;
    }
  | undefined
>(undefined);

export const AppGlobalStateProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [noticeboardApp, setNoticeboardApp] = useState<NoticeboardApp>(
    defaultNoticeboardApp,
  );
  const [algorandClient, setAlgorandClient] = useState<AlgorandClient>(
    defaultAlgorandClient,
  );
  const [valAdsMap, setValAdsMap] = useState< Map<bigint, ValidatorAdGlobalState> | undefined >(undefined);
  const [valOwnersAdsMap, setValOwnersAdsMap] = useState< Map<string, bigint[]> | undefined >(undefined);
  const [stakingData, setStakingData] = useState<StakingData | undefined>(undefined);

  //Fetching Noticeboard GlobalState
  useEffect(() => {
    const fetchNBGS = async () => {
      const res = await NoticeboardGlobalState.getGlobalState(
        noticeboardApp.client,
      );
      setNoticeboardApp((prev) => {
        console.log("Noticeboard App Set");
        return { ...prev, globalState: res };
      });
    };

    fetchNBGS();
  }, []);

  //Fetching all Validators Owners and all their Ads
  useEffect(() => {
    const fetch = async () => {
      if (noticeboardApp.globalState != undefined) {
        // Fetch all Validator Owners' information
        const validators = await fetchAllVal(
          algorandClient.client.algod,
          noticeboardApp.globalState,
        );

        // Keep just app IDs
        const validatorsMapped = new Map(
          Array.from(validators || [],([address, userInfo]) => [
            address,
            userInfo.appIds.filter(appId => appId !== 0n),
          ])
        );

        console.log("Validator Owners Map ::", validatorsMapped);
        setValOwnersAdsMap(validatorsMapped);

        // Fetch all Ads of all Validator Owners
        const valAdIds = Array.from(validatorsMapped.values()).flatMap(appIds => appIds);

        const res = await fetchValidatorAds(
          algorandClient.client.algod,
          valAdIds,
        )

        setValAdsMap(() => {
          console.log("Ad Map Set");
          console.log("Ads Map ::", res);
          return res;
        });
      }
    };

    fetch();
  }, [noticeboardApp]);

  // Get staking data
  useEffect(() => {
    const fetchStakingData = async () => {
      try {
        const props = {
          headers: { "Accept": "*/*" },
        };
        // Fetch info about number of nodes
        const data1 = await fetch(`${apiStakingDataSource}/v1/delayed/network/nodes/count`, props).then((res) => res.json());
        const nodesTotal = data1["nodes"];

        // Fetch info about online stake
        const data2 = await fetch(`${apiStakingDataSource}/v1/realtime/participation/online`, props).then((res) => res.json());
        const accountsOnlineAll = data2["online"];
        const accountsOnline30k = data2["online_above30k"];
        const stakeOnline = data2["stake_micro_algo"];
        const round = await ParamsCache.getRound();
        const apy = estimateAPY(round, stakeOnline);

        setStakingData({ nodesTotal, accountsOnlineAll, accountsOnline30k, stakeOnline, apy });
      } catch (error) {
        console.error('Error fetching staking data:', error);
      }
    }

    fetchStakingData();
  }, []);

  return (
    <AppGlobalStateContext.Provider
      value={{ noticeboardApp, algorandClient, valAdsMap, valsMap: valOwnersAdsMap, stakingData }}
    >
      {children}
    </AppGlobalStateContext.Provider>
  );
};

export function useAppGlobalState() {
  const context = useContext(AppGlobalStateContext);
  if (context === undefined) {
    throw new Error("useGlobalState must be used within a GlobalStateProvider");
  }
  return context;
}
