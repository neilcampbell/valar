import { Container } from "@/components/Container/Container";

import { useEffect, useState } from "react";
import { fetchDelegatorContracts } from "@/api/queries/delegator-contracts";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import CannotStakeCard from "./SummaryCard/CannotStakeCard";
import DetailsCard from "./DetailsCard/DetailsCard";
import ContractActiveCard from "./SummaryCard/ContractActiveCard";
import ConnectWalletCard from "./SummaryCard/ConnectWalletCard";
import ContractCreateCard from "./SummaryCard/ContractCreateCard";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { fetchValidatorAds } from "@/api/queries/validator-ads";
import { useWallet } from "@txnlab/use-wallet-react";
import { canStake } from "@/utils/convert";
import useUserStore from "@/store/userStore";
import { StakeReqs } from "@/lib/types";
import { FETCH_INTERVAL } from "@/constants/timing";

const styleContents = "grid gap-3 lg:grid-cols-5";
const styleLeft = "lg:col-span-3 h-min rounded-lg border border-border bg-background-light p-3";
const styleRight = "lg:col-span-2 h-min rounded-lg bg-gradient-to-br from-gradient-light to-gradient-dark p-3";

const Contents = ({
  delAppId,
  valAppId,
  stakeReqs,
  open,
  onOpenChange,
}: {
  delAppId?: bigint;
  valAppId?: bigint;
  stakeReqs?: StakeReqs;
  open?: boolean;
  onOpenChange: React.Dispatch<React.SetStateAction<boolean | undefined>>;
}) => {

  const { algorandClient } = useAppGlobalState();
  const { activeAddress } = useWallet();
  const { user } = useUserStore();
  const [gsDelCo, setGsDelCo] = useState<DelegatorContractGlobalState | undefined>(undefined);
  const [gsValAd, setGsValAd] = useState<ValidatorAdGlobalState | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [possible, setPossible] = useState<boolean>(false);
  const [_delAppId, setDelAppId] = useState<bigint | undefined>(delAppId);
  const [refetch, setRefetch] = useState<boolean>(true);
  const drawerClose = () => onOpenChange(false);


  // -----------------------------------
  // Periodically fetch data or when delAppId or open status change
  useEffect(() => {
    // Fetch data
    const fetch = async () => {
      console.log("Trying to fetch data...");
      if(open && refetch){
        console.log("Fetching data...");

        if(_delAppId){
          // Fetch delegator contract and its validator ad
          try{
            const resDelCo = await fetchDelegatorContracts(algorandClient.client.algod, [_delAppId]);
            const gsDelCo = resDelCo!.get(_delAppId);

            console.log("Delegator Contract ::", _delAppId, gsDelCo);
            setGsDelCo(gsDelCo);

            const valAppId = gsDelCo!.validatorAdAppId;
            const resValAd = await fetchValidatorAds(algorandClient.client.algod, [valAppId]);
            const gsValAd = resValAd!.get(valAppId);

            console.log("Validator Ad ::", valAppId, gsValAd);
            setGsValAd(gsValAd);
            // TO DO: Update global storage of valAdMap
          } catch {
            setGsDelCo(undefined);
          }
        } else if(valAppId) {
          // Fetch validator ad
          try{
            const resValAd = await fetchValidatorAds(algorandClient.client.algod, [valAppId]);
            const gsValAd = resValAd!.get(valAppId);

            console.log("Validator Ad ::", valAppId, gsValAd);
            setGsValAd(gsValAd);
            // TO DO: Update global storage of valAdMap
          } catch {
            setGsValAd(undefined);
          }
        }

        setRefetch(false);
      }
      setLoading(false);
    };

    fetch(); // Fetch immediately when component mounts or parameter changes

    const interval = setInterval(() => {
      setRefetch(true);
      fetch();
    }, FETCH_INTERVAL); // Fetch at a regular interval

    return () => clearInterval(interval); // Clear interval on unmount or parameter change
  }, [_delAppId, refetch, open]); // Dependency on parameters
  // -----------------------------------


  useEffect(() => {
    if (gsValAd && user && stakeReqs){
      const possible = canStake(gsValAd, user, stakeReqs);
      setPossible(possible);
    }
  }, [gsValAd, user, stakeReqs]);

  if (loading) {
    return (
      <Container>
        <p>Loading...</p>
      </Container>
    );
  }

  if (!gsValAd) {
    return (
      <Container>
        <p>Unable to fetch validator ad details.</p>
      </Container>
    );
  }

  // There is an active delegator contract
  if(_delAppId){
    if(gsDelCo){
      return(
        // Display the contract details
        // and correct interaction options
        <Container>
          <div className={styleContents} >
            <DetailsCard className={styleLeft} gsDelCo={gsDelCo} gsValAd={gsValAd} />
            <ContractActiveCard className={styleRight} gsDelCo={gsDelCo} gsValAd={gsValAd} yourStake={user!.algo} drawerClose={drawerClose} setRefetch={setRefetch}/>
          </div>
        </Container>
      );
    } else {
      return (
        <Container>
          <p>Unable to fetch delegator contract details.</p>
        </Container>
      );
    }
  } else {
    // A new delegator contract is being created
    if(!activeAddress){
      return (
        // Display ad details as there is no wallet connected,
        // and prompt to connect it
        <Container>
          <div className={styleContents} >
            <DetailsCard className={styleLeft} gsDelCo={undefined} gsValAd={gsValAd}/>
            <ConnectWalletCard className={styleRight} drawerClose={drawerClose} />
          </div>
        </Container>
      );
    } else {
        if(possible){
          return (
            // Display ad details tailored to user,
            // and allow creation of new delegator contract if requirements are met
            <Container>
              <div className={styleContents} >
                <DetailsCard className={styleLeft} gsDelCo={undefined} gsValAd={gsValAd} stakeReqs={stakeReqs} />
                <ContractCreateCard className={styleRight} stakeReqs={stakeReqs!} gsValAd={gsValAd} setDelAppId={setDelAppId} setRefetch={setRefetch}/>
              </div>
            </Container>
          );
        } else {
          // Display ad details tailored to user
          // and display why it is not possible to create a delegator contract
          return (
            <Container>
              <div className={styleContents} >
                <DetailsCard className={styleLeft} gsDelCo={undefined} gsValAd={gsValAd} stakeReqs={stakeReqs} />
                <CannotStakeCard className={styleRight} />
              </div>
            </Container>
          );
        }
    }
  }

};

export default Contents;
