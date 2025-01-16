import { ValAdStatus } from "@/lib/types";
import StatusCell from "../DataTable/StatusCell";

const AdStatus = ({
  status,
}: {
  status: ValAdStatus;
}) => {
  if (status === "CREATED")
    return <StatusCell status="Created" className="bg-secondary" />;
  if (status === "NOT_LIVE")
    return <StatusCell status="Not Live" className="bg-error" />;
  if (status === "NOT_READY")
    return <StatusCell status="Not Ready" className="bg-warning" />;
  if (status === "READY")
    return <StatusCell status="Ready" className="bg-success" />;
};

export default AdStatus;
