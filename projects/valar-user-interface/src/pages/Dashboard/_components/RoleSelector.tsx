import { useNavigate } from "react-router-dom";

import { Button } from "../../../components/ui/button";
import { ROLE_VAL_STR } from "@/constants/smart-contracts";

const RoleSelector = ({ setRole }: { setRole: React.Dispatch<React.SetStateAction<string | undefined>> }) => {
  const navigate = useNavigate();
  return (
    <div className="lg:mt-20 flex justify-center items-center">
      <div className="max-w-[900px]">
        <div className="my-6 flex flex-col items-center">
          <h1 className="text-xl font-bold">Select Your Role</h1>
          <h3 className="text-sm text-text-tertiary">
            Please select one of the two roles below.
          </h3>
        </div>
        <div className="flex flex-wrap gap-4 lg:flex-nowrap">
          <div className="flex w-full flex-col justify-between gap-3 rounded-lg bg-background-light p-6 lg:flex-1">
            <div className="flex flex-col gap-1">
              <h3 className="text-xs font-semibold text-secondary-dark lg:text-sm">
                ALGORAND USER
              </h3>
              <h1 className="font-bold">Do you have Algorand?</h1>
              <p className="text-sm text-text-tertiary">
                You can stake it to earn staking rewards, protect your assets,
                and decentralize the network.
              </p>
            </div>
            <Button
              className="mt-6 w-full"
              variant={"v_secondary"}
              onClick={() => navigate("/stake")}
            >
              Start Staking
            </Button>
          </div>

          <div className="flex w-full flex-col justify-between gap-3 rounded-lg bg-background-light p-6 lg:flex-1">
            <div className="flex flex-col gap-1">
              <p className="font-semibol text-xs text-tertiary lg:text-sm">
                NODE RUNNER
              </p>
              <h1 className="font-bold">
                Do you run an Algorand node or want to?
              </h1>
              <p className="text-sm text-text-tertiary">
                Maximize its utilization and your revenue by letting others
                stake with you, contributing to network's decentralization.
              </p>
            </div>
            <Button
              className="mt-6 w-full bg-tertiary-dark"
              variant={"v_tertiary"}
              onClick={() => setRole(ROLE_VAL_STR)}
            >
              Run a Node
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoleSelector;
