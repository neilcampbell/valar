import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const LearnMoreCard = () => {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border bg-background-light p-2">
      <p className="text-sm">
        Learn to set up a node and automate user servicing.
      </p>
      <Link to={"/learn-node"}>
        <Button variant={"v_link"} className="px-2 text-text-tertiary">
          Learn More
        </Button>
      </Link>
    </div>
  );
};

export default LearnMoreCard;
