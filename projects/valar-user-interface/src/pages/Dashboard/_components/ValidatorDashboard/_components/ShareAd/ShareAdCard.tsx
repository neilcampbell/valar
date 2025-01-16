import { Button } from "@/components/ui/button";
import { Link } from "lucide-react";

const ShareAdCard = () => {
  return (
    <div className="flex items-center justify-between gap-2 rounded-lg bg-background-light p-3">
      <h3 className="text-sm">Share your ads.</h3>
      <Button variant={"v_outline"} className="border-0 px-2">
        <Link /> Copy Link
      </Button>
    </div>
  );
};

export default ShareAdCard;
