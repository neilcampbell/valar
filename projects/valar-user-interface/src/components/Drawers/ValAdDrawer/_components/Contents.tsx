
import { fetchValidatorAds } from "@/api/queries/validator-ads";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useEffect, useState } from "react";
import InfoCard from "./InfoCard";
import EarningsCard from "./EarningsCard";
import PublishAndPayCard from "./PublishAndPayCard";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { ValAdToForm } from "@/utils/convert";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { Separator } from "@/components/ui/separator";
import { adFormSchema } from "@/lib/form-schema";
import { z } from "zod";
import GraphWidget from "./GraphWidget";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import EditCard from "./EditCard";
import { AD_FORM_DEFAULTS, CURRENCIES } from "@/constants/platform";
import PricingSection from "./AdForm/AdFormSections/PricingSection";
import StakeLimitSection from "./AdForm/AdFormSections/StakeLimitsSection";
import WarningsSection from "./AdForm/AdFormSections/WarningsSection";
import TimingsSection from "./AdForm/AdFormSections/TimingsSection";
import EligibilitySection from "./AdForm/AdFormSections/EligibilitySection";
import OperationalConfigSection from "./AdForm/AdFormSections/OperationalConfigSection";
import { useWatch } from "react-hook-form";
import { AdFormValuesDisplay } from "@/lib/types";

const Contents = ({
  valAppId,
  onOpenChangeDrawer,
}: {
  valAppId?: bigint,
  onOpenChangeDrawer: () => void,
}) => {

  const { algorandClient } = useAppGlobalState();

  const [gsValAd, setGsValAd] = useState<ValidatorAdGlobalState | undefined>(undefined);
  const [isEditing, setIsEditing] = useState<boolean>(!valAppId);

  const formAdCreateDefaults = {...AD_FORM_DEFAULTS, paymentCurrency: AD_FORM_DEFAULTS.paymentCurrency.toString()};
  const [formDefaults, setFormDefaults] = useState<AdFormValuesDisplay>(formAdCreateDefaults);

  // Define form
  const form = useForm<z.infer<typeof adFormSchema>>({
    resolver: zodResolver(adFormSchema),
    defaultValues: formDefaults,
    mode:"all",
  });

  const paymentCurrency = useWatch({ control: form.control, name: "paymentCurrency" });

  // Modify adFormSchema defaults depending on selected currency
  useEffect(() => {
    const suggestedDefaults = {
      ...form.getValues(),
      ...CURRENCIES.get(BigInt(paymentCurrency))!.adTermsFees,
    };

    form.reset({...suggestedDefaults, paymentCurrency: suggestedDefaults.paymentCurrency.toString()});
  }, [paymentCurrency]);

  // Fetching Validator Ad
  useEffect(() => {
    const fetch = async () => {
      if(valAppId){
        console.log(`Fetching validator ad with ID: ${valAppId}.`);
        try {
          const res = await fetchValidatorAds(algorandClient.client.algod, [valAppId]);

          if(res){
            const gsValAd = res.get(valAppId)!;

            console.log("Validator Ad ::", gsValAd);
            setGsValAd(gsValAd);

            const formValues = await ValAdToForm(gsValAd);
            const formDefaults = {...formValues, paymentCurrency: formValues.paymentCurrency.toString()};
            setFormDefaults(formDefaults);
            form.reset(formDefaults);
          } else {
            setGsValAd(undefined);
            setFormDefaults(formAdCreateDefaults);
          }
        } catch {
          setGsValAd(undefined);
          setFormDefaults(formAdCreateDefaults);
        }
      } else {
        setGsValAd(undefined);
        setFormDefaults(formAdCreateDefaults);
      }
    }

    fetch();
  }, [valAppId]);


  //Submit Handler
  function onSubmit(values: z.infer<typeof adFormSchema>) {
    console.log(values);
  }



  return (
    <div className="flex flex-wrap-reverse lg:flex-nowrap gap-4">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          <div className={`${!gsValAd ? "flex flex-wrap lg:flex-nowrap gap-6" : "flex-1"}`} >
            <div>
              <div className={`${!gsValAd ? "grid grid-cols-1 gap-6 lg:grid-cols-2" : "grid lg:grid-cols-2 gap-6"}`}>
                <div className="space-y-8">
                  <PricingSection form={form} disabled={!isEditing} />
                  <StakeLimitSection form={form} disabled={!isEditing} />
                  <TimingsSection form={form} disabled={!isEditing} />
                </div>
                <div className="flex flex-col justify-between gap-8">
                  <GraphWidget form={form} />

                  <div className="w-full space-y-8">
                    <WarningsSection form={form} disabled={!isEditing} />
                    <EligibilitySection form={form} disabled={!isEditing} />
                  </div>
                </div>
              </div>
              {(!gsValAd || isEditing) &&
                <div className="flex w-full justify-end">
                  <Button
                    type="button"
                    variant={"v_link"}
                    className="text-text underline"
                    onClick={() => form.reset({...formAdCreateDefaults, managerAddress: formDefaults.managerAddress})}
                  >
                    Set to Default
                  </Button>
                </div>
              }
              <Separator className="my-4" />
              <div>
                <OperationalConfigSection form={form} disabled={!isEditing} />
              </div>
            </div>
            {gsValAd &&
              <EditCard isEditing={isEditing} setIsEditing={setIsEditing} form={form} gsValAd={gsValAd} onOpenChangeDrawer={onOpenChangeDrawer}/>
            }
          </div>
        </form>
      </Form>
      <div className="flex flex-col gap-2 lg:min-w-[250px]">
        <div className="flex gap-2 lg:flex-col">
          {!gsValAd ? (
            <PublishAndPayCard form={form} onOpenChangeDrawer={onOpenChangeDrawer} />
          ) : (
            <>
              <InfoCard gsValAd={gsValAd} />
              <EarningsCard gsValAd={gsValAd} />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Contents;
