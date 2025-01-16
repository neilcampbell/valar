import { DelCoStatus } from "@/lib/types";
import StatusCell from "../DataTable/StatusCell";

const ContractStatus = ({
  status,
  extStatusText,
}: {
  status: DelCoStatus;
  extStatusText?: string;
}) => {
  if (status === "LIVE")
    return <StatusCell status="Live" className="bg-success" />;
  if (status === "AWAITING_SETUP")
    return <StatusCell status={!extStatusText ? "Awaiting setup" :  "Awaiting setup" + extStatusText} className="bg-warning" />;
  if (status === "CONFIRM_SETUP")
    return <StatusCell status={!extStatusText ? "Confirm setup" : "Confirm setup" + extStatusText} className="bg-secondary" />;
  if (status === "ENDED")
    return <StatusCell status={!extStatusText ? "Ended" : "Ended" + extStatusText} className="bg-error" />;
};

export default ContractStatus;
