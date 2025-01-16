import { adTermsAndConfig } from "@/api/contract/ValidatorAdCalls";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import useUserStore from "@/store/userStore";
import { formToTermsAndConfig, hexToBytes } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { useState } from "react";
import { UseFormReturn } from "react-hook-form";
import TermsAndConditions from "@/components/TermsAndConditions/TermsAndConditions";
import { TC_LATEST } from "@/constants/terms-and-conditions";
import { notify } from "@/components/Notification/notification";


const EditCard = ({
  isEditing,
  setIsEditing,
  form,
  gsValAd,
  onOpenChangeDrawer,
}: {
  isEditing: boolean,
  setIsEditing: React.Dispatch<React.SetStateAction<boolean>>,
  form: UseFormReturn<any>,
  gsValAd: ValidatorAdGlobalState,
  onOpenChangeDrawer: () => void,
}) => {
  const [termsChecked, setTermsChecked] = useState<boolean>(false);
  const { activeAddress, transactionSigner } = useWallet();
  const { user } = useUserStore();
  const { algorandClient, noticeboardApp } = useAppGlobalState();

  const handleConfigure = async () => {
    console.log("Editing ad...");

    try{
      const { terms, config } = await formToTermsAndConfig(form.getValues(), noticeboardApp!.globalState!);
      const tcSha256 = hexToBytes(TC_LATEST)

      const res = await adTermsAndConfig({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsValAd: gsValAd,
        userAddress: activeAddress!,
        userInfo: user?.userInfo!,
        valAppId: gsValAd.appId,
        terms: terms,
        tcSha256: tcSha256,
        config: config,
        signer: transactionSigner,
      });

      console.log(res.transactions[0].txID());
      notify({ title: "Ad edited successfully", variant: "success" });
      // If successful ad configuration, close drawer
      onOpenChangeDrawer()
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Ad edit failed", variant: "error" });
    }
  }

  return (
    <div>
      {!isEditing ? (
        <Button
          type="button"
          variant={"v_secondary"}
          className="w-full lg:w-auto"
          onClick={() => setIsEditing(true)}
        >
          Edit Configuration
        </Button>
      ) : (
        <div>
          <div>
            <Checkbox
              onCheckedChange={(v) =>
                setTermsChecked(v === "indeterminate" ? false : v)
              }
            />{" "}
            <label className="ml-2 text-sm">
              I have read, understand, and agree with <TermsAndConditions terms={TC_LATEST}/>.
            </label>
          </div>
          <div className="mt-4 flex gap-10">
            <Button
              variant={"v_secondary"}
              disabled={!termsChecked || ((!form.formState.isValid) && form.formState.isDirty)}
              onClick={handleConfigure}>
              Save Configuration
            </Button>
            <Button
              type="button"
              variant={"v_link"}
              onClick={() => {
                setIsEditing(false);
                setTermsChecked(false);
                onOpenChangeDrawer();
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default EditCard;
