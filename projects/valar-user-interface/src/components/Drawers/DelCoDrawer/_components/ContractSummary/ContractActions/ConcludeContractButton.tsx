import { DelegatorApiCall } from "@/api/contract/DelegatorCall";
import { GovernanceApi } from "@/api/governance.api";
import { notify } from "@/components/Notification/notification";
import ContractCreationWarningPopup from "@/components/Popup/ContractCreationWarningPopup";
import { LoadingButton } from "@/components/ui/button";
import { FEE_OPT_IN_PERFORMANCE_TRACKING, MIN_ALGO_STAKE_FOR_REWARDS } from "@/constants/smart-contracts";
import { DC_STATE_ENDED_MASK } from "@/constants/states";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useDelCoDrawer } from "@/contexts/DelCoDrawerContext";
import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { ContractWarning } from "@/lib/contract-warnings";
import useTxnLoader from "@/store/txnLoaderStore";
import useUserStore from "@/store/userStore";
import { bytesToStr } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { useEffect, useState } from "react";

const ConcludeContractButton = ({
  termsChecked,
  role,
  maxStakeAdjusted,
  algoPayment,
}: {
  termsChecked: boolean;
  role: string;
  maxStakeAdjusted: bigint;
  algoPayment: number;
}) => {
  const { algorandClient, noticeboardApp, renewDelCo, valAdsMap } = useAppGlobalState();
  const { activeAddress, transactionSigner } = useWallet();
  const { user } = useUserStore();
  const { setDelAppId, gsValAd, gsDelCo, setRefetch, stakeReqs, setIsRenewSuccess } = useDelCoDrawer();

  const { txnLoading, setTxnLoading } = useTxnLoader();

  const [openWarning, setOpenWarning] = useState<boolean>(false);
  const [warnings, setWarnings] = useState<ContractWarning[]>([]);

  const _gsDelCo = renewDelCo ? renewDelCo : gsDelCo;
  const partner = undefined;

  /**
   * ======================================
   *     Check if user should be warned
   * ======================================
   */
  useEffect(() => {
    const fetch = async () => {
      if (user) {
        let warnings: ContractWarning[] = [];

        // If beneficiary is also the manager, the whole algoPayment amount is paid by it
        let payment = user.address === user.beneficiary.address ? algoPayment : 0;

        // If beneficiary is not yet tracked and is not an gALGO escrow,
        // the beneficiary will have to pay the higher key reg fee directly.
        payment =
          user.beneficiary.trackedPerformance || user.beneficiary.address === user.galgo?.address
            ? payment
            : payment + FEE_OPT_IN_PERFORMANCE_TRACKING;

        // Get beneficiary's governance commitment
        const algoCommitment = await GovernanceApi.fetchGovCommitment(user.beneficiary.address);

        // Check if beneficiary will fall out of governance
        if (algoCommitment && Number(user.beneficiary.algo) - payment < Number(algoCommitment))
          warnings.push({ type: "governance-commitment", param: algoCommitment });

        // Check if beneficiary is below staking rewards limit.
        if (Number(user.beneficiary.algo) < MIN_ALGO_STAKE_FOR_REWARDS) {
          warnings.push({ type: "rewards-base" });
        } else if (Number(user.beneficiary.algo) - payment < MIN_ALGO_STAKE_FOR_REWARDS) {
          // Check if the payment will move the beneficiary below staking rewards limit.
          warnings.push({ type: "rewards-pay" });
        }

        // Check if a contract already exists for this beneficiary by this manager
        const contractAlreadyExists = !!Array.from(
          ((user.userApps as Map<bigint, DelegatorContractGlobalState>) ?? []).values(),
        ).find((gsDelCo) => {
          return (
            gsDelCo.delBeneficiary === user.beneficiary.address &&
            bytesToStr(gsDelCo.stateCur) < bytesToStr(DC_STATE_ENDED_MASK)
          );
        });

        if (contractAlreadyExists && !renewDelCo) warnings.push({ type: "existing-contract" });

        setWarnings(warnings);
        console.log("warnings: ", warnings);
      }
    };

    fetch();
  }, [user, renewDelCo, stakeReqs, algoPayment]);

  /**
   * =================================
   *     Handle Contract Conclude
   * =================================
   */

  const handleConclude = async () => {
    console.log("Submit txn");

    if (!gsValAd) return console.log("ValAd GS not found");

    setTxnLoading(true);
    if (role === "") {
      try {
        const res = await DelegatorApiCall.userCreateAndContractCreate({
          algorandClient: algorandClient,
          noticeBoardClient: noticeboardApp.client,
          gsNoticeBoard: noticeboardApp!.globalState!,
          gsValidatorAd: gsValAd,
          userAddress: activeAddress!,
          maxStake: maxStakeAdjusted,
          duration: stakeReqs!.duration,
          delBeneficiary: user!.beneficiary!.address,
          partner: partner,
          signer: transactionSigner,
        });

        if (res.returns[2]) {
          console.log("Created contract with ID: " + res.returns[2]);
          console.log(res.transactions[0].txID());

          // // Fetch userInfo and set it to UserStore
          // const userInfo = await UserInfo.getUserInfo(algorandClient.client.algod, activeAddress!);
          // setUser({ ...user!, userInfo: userInfo });

          setDelAppId(res.returns[2]);
          setRefetch(true);
        }
      } catch (error) {
        console.error("Error in submit:", error);
      }
    } else {
      try {
        const res = await DelegatorApiCall.contractCreate({
          algorandClient: algorandClient,
          noticeBoardClient: noticeboardApp.client,
          gsNoticeBoard: noticeboardApp!.globalState!,
          gsValidatorAd: gsValAd,
          userAddress: activeAddress!,
          maxStake: maxStakeAdjusted,
          duration: stakeReqs!.duration,
          delBeneficiary: user!.beneficiary!.address,
          partner: partner,
          delUserInfo: user?.userInfo!,
          signer: transactionSigner,
        });

        if (res.returns[1]) {
          console.log("Created contract with ID: " + res.returns[1]);
          console.log(res.transactions[0].txID());
          notify({
            title: "Contract created. Please wait ...",
            description: "Please wait for node setup and confirm it to start staking.",
            variant: "info",
            duration: 12000,
            onMountDismiss: ["txnLoading"],
          });

          // // Contract creation was successful
          // // Update userInfo without need for refetch
          // const updatedAppIds = [...user!.userInfo!.appIds];
          // const idx = user!.userInfo!.getFreeAppIndex();  // Know where it is stored
          // updatedAppIds[idx] = res.returns[1];
          // setUser({ ...user!, userInfo: new UserInfo({ ...user!.userInfo!, appIds: updatedAppIds}) });

          setDelAppId(res.returns[1]);
          setRefetch(true);
        }
      } catch (error) {
        console.error("Error in submit:", error);
        notify({ title: "Contract creation failed", variant: "error", onMountDismiss: ["txnLoading"] });
      }
    }
    setTxnLoading(false);

    console.log("Submitted txn");
  };

  /**
   * ==============================
   *     Handle Contract Renew
   * ==============================
   */

  const handleRenew = async () => {
    console.log("Submit txn");

    if (!gsValAd) return console.log("ValAd GS not found");
    if (!_gsDelCo) return console.log("DelCo GS not found");

    const gsValAdOld = valAdsMap?.get(_gsDelCo.validatorAdAppId);
    if (!gsValAdOld) return console.log("Old ValAd GS not found");

    setTxnLoading(true);
    try {
      const res = await DelegatorApiCall.contractRenew({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsNoticeBoard: noticeboardApp!.globalState!,
        gsValAdOld: gsValAdOld,
        gsValAdNew: gsValAd,
        gsDelCo: _gsDelCo,
        user: user!,
        maxStake: maxStakeAdjusted,
        duration: stakeReqs!.duration,
        delBeneficiary: user!.beneficiary!.address,
        partner: partner,
        delUserInfo: user?.userInfo!,
        signer: transactionSigner,
      });

      const createdAppId = res.returns[res.returns.length - 1];
      if (createdAppId) {
        console.log("Created contract with ID: " + createdAppId);
        console.log(res.transactions[0].txID());
        notify({
          title: "Contract renewed. Please wait ...",
          description: "Please wait for new node setup and confirm it to continue staking.",
          variant: "info",
          duration: 12000,
          onMountDismiss: ["txnLoading"],
        });
        // // Contract creation was successful
        // // Update userInfo without need for refetch
        // const updatedAppIds = [...user!.userInfo!.appIds];
        // const idx = user!.userInfo!.getFreeAppIndex();  // Know where it is stored
        // updatedAppIds[idx] = res.returns[1];
        // setUser({ ...user!, userInfo: new UserInfo({ ...user!.userInfo!, appIds: updatedAppIds}) });

        //Set true to signal renewal was successfull
        setIsRenewSuccess(true);

        setDelAppId(createdAppId);
        setRefetch(true);
      }
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Contract renewal failed", variant: "error", onMountDismiss: ["txnLoading"] });
    }
    setTxnLoading(false);

    console.log("Submitted txn");
  };

  const handleSubmit = renewDelCo ? handleRenew : handleConclude;

  return (
    <div>
      <LoadingButton
        loading={txnLoading}
        variant={"v_primary"}
        className="w-full"
        disabled={!termsChecked || txnLoading}
        onClick={warnings.length > 0 ? () => setOpenWarning(true) : handleSubmit}
      >
        {renewDelCo ? "Renew" : "Conclude"} Contract & Pay
      </LoadingButton>
      <ContractCreationWarningPopup
        onSubmit={handleSubmit}
        openWarning={openWarning}
        setOpenWarning={setOpenWarning}
        warnings={warnings}
      />
    </div>
  );
};

export default ConcludeContractButton;
