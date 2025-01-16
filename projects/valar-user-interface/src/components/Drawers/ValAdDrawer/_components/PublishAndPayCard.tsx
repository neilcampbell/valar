import { adCreate, adTermsAndConfig, userCreateAndAdCreate } from "@/api/contract/ValidatorAdCalls";
import ConfigureAdPopup from "@/components/Popup/ConfigureAdPopup";
import ITooltip from "@/components/Tooltip/ITooltip";
import { Wallet } from "@/components/Wallet/Wallet";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE, MBR_USER_BOX, ROLE_DEL_STR } from "@/constants/smart-contracts";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { UserInfo } from "@/interfaces/contracts/User";
import { ToolTips } from "@/constants/tooltips";
import useUserStore from "@/store/userStore";
import { algoBigIntToDisplay, formToTermsAndConfig, hexToBytes } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { useEffect, useState } from "react";
import { UseFormReturn } from "react-hook-form";
import TermsAndConditions from "@/components/TermsAndConditions/TermsAndConditions";
import { TC_LATEST } from "@/constants/terms-and-conditions";
import { ALGORAND_DEPOSIT_DECIMALS } from "@/constants/units";
import { notify } from "@/components/Notification/notification";

const PublishAndPayCard = ({
  form,
  onOpenChangeDrawer,
}: {
  form: UseFormReturn<any>;
  onOpenChangeDrawer: () => void;
}) => {
  const [termsChecked, setTermsChecked] = useState<boolean>(false);
  const { activeAddress, transactionSigner } = useWallet();
  const { user, setUser } = useUserStore();
  const { algorandClient, noticeboardApp } = useAppGlobalState();

  const [role, setRole] = useState<string>("");
  const [algoDeposit, setAlgoDeposit] = useState<number>(MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE + MBR_USER_BOX);

  const [preparingAd, setPreparingAd] = useState<boolean>(false);
  const [createdAppId, setCreatedAppId] = useState<bigint>(0n);

  const valRegFee = noticeboardApp.globalState!.noticeboardFees.valUserReg
  const valCreateFee = noticeboardApp.globalState!.noticeboardFees.valAdCreation

  useEffect(() => {
    //Get user role
    if (user) {
      if(user.userInfo){
        const role = new TextDecoder().decode(new Uint8Array(user.userInfo.role));
        setRole(role);
        setAlgoDeposit(MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE);
      } else {
        setRole("");
        setAlgoDeposit(MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE + MBR_USER_BOX);
      }
    } else {
      setRole("");
      setAlgoDeposit(MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE + MBR_USER_BOX);
    }
  }, [activeAddress]);

  const handleCreate = async () => {
    console.log("Submit txn");

    if (role === "") {
      try {
        const res = await userCreateAndAdCreate({
          algorandClient: algorandClient,
          noticeBoardClient: noticeboardApp.client,
          gsNoticeBoard: noticeboardApp!.globalState!,
          userAddress: activeAddress!,
          signer: transactionSigner,
        });

        console.log("Created ad with ID: " + res.returns[1]);
        console.log(res.transactions[0].txID());

        if (res.returns[1]) {
          // User and ad creation was successful
          // Fetch userInfo (FOR FUTURE: Could simplify user to have just appIds instead of userInfo, and here do manual modification instead of re-fetch)
          const userInfo = await UserInfo.getUserInfo(algorandClient.client.algod, activeAddress!);
          setUser({ ...user!, userInfo: userInfo });
          // Continue with configuration through popup
          setPreparingAd(true);
          setCreatedAppId(res.returns[1]);
          notify({ title: "Ad created successfully", variant: "success" });

        }
      } catch (error) {
        console.error("Error in submit:", error);
        notify({ title: "Ad creation failed", variant: "error" });
      }
    } else {
      try {
        const res = await adCreate({
          algorandClient: algorandClient,
          noticeBoardClient: noticeboardApp.client,
          gsNoticeBoard: noticeboardApp!.globalState!,
          userAddress: activeAddress!,
          userInfo: user?.userInfo!,
          signer: transactionSigner,
        });

        console.log("Created ad with ID: " + res.return);
        console.log(res.transactions[0].txID());
        notify({ title: "Ad created successfully", variant: "success" });

        if (res.return) {
          // Ad creation was successful
          // Update userInfo without need for refetch
          const updatedAppIds = [...user!.userInfo!.appIds];
          const idx = user!.userInfo!.getFreeAppIndex();  // Know where it is stored
          updatedAppIds[idx] = res.return;
          setUser({ ...user!, userInfo: new UserInfo({ ...user!.userInfo!, appIds: updatedAppIds}) });
          // Continue with configuration through popup
          setPreparingAd(true);
          setCreatedAppId(res.return);
        }
      } catch (error) {
        console.error("Error in submit:", error);
        notify({ title: "Ad creation failed", variant: "error" });
      }
    }

    console.log("Submitted txn");
  }

  const handleConfigure = async () => {
    try {
      const { terms, config } = await formToTermsAndConfig(form.getValues(), noticeboardApp!.globalState!);
      const tcSha256 = hexToBytes(TC_LATEST);

      const res = await adTermsAndConfig({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsValAd: undefined,
        userAddress: activeAddress!,
        userInfo: user?.userInfo!,
        valAppId: createdAppId,
        terms: terms,
        tcSha256: tcSha256,
        config: config,
        signer: transactionSigner,
      });

      console.log(res.transactions[0].txID());

      // If successful ad configuration, close popup
      setPreparingAd(false);
      notify({ title: "Ad configured successfully", variant: "success" });
      
      // Close drawer
      onOpenChangeDrawer();

    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Ad configuration failed", variant: "error" });
    }
  }

  if (role === ROLE_DEL_STR) {
    return (
      <div className="rounded-lg border border-border bg-background-light p-3">
        <div className="space-y-1">
          <div className="flex gap-1 text-sm">
            Your address is already registered as Algorand user for staking. <br />
            Please use a different address to become a node runner.
          </div>
          <Wallet className="mt-4 w-full" />
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-border bg-background-light p-3">
      <div className="space-y-1">
        {role === "" && <div className="flex gap-1 text-sm">
          <div>First-time registration fee:</div>
          <div>{algoBigIntToDisplay(valRegFee, "none", true, ALGORAND_DEPOSIT_DECIMALS)}</div>
        </div>}
        <div className="flex gap-1 text-sm">
          <div>Ad creation fee:</div>
          <div>{algoBigIntToDisplay(valCreateFee, "none", true, ALGORAND_DEPOSIT_DECIMALS)}</div>
        </div>
        <div className="flex gap-1 text-sm">
          <div className="flex items-center gap-1">
            Algorand deposit <ITooltip value={role==="" ? ToolTips.AlgorandDepositUserAndVal : ToolTips.AlgorandDepositVal} /> :
          </div>
          <div>{algoBigIntToDisplay(BigInt(algoDeposit), "none", true, ALGORAND_DEPOSIT_DECIMALS)}</div>
        </div>
      </div>
      <div className="mt-6 flex space-x-2">
        <Checkbox
          onCheckedChange={(v) =>
            setTermsChecked(v === "indeterminate" ? false : v)
          }
        />
        <Label className="text-sm font-normal">
          I have read, understand, and agree with <TermsAndConditions terms={TC_LATEST}/>.
        </Label>
      </div>
      {activeAddress ?
      (
          <Button
            type="submit"
            variant={"v_primary"}
            className="mt-4 w-full"
            disabled={!termsChecked || ((!form.formState.isValid) && form.formState.isDirty)}
            onClick={handleCreate}
          >
            Publish & Pay
          </Button>
        ) : (
          <Wallet className="mt-4 w-full" text={"Connect Wallet to Continue"} />
        )
      }
      <div><ConfigureAdPopup isOpen={preparingAd} setOpen={setPreparingAd} handleConfigure={handleConfigure}/></div>
    </div>
  );
};

export default PublishAndPayCard;
