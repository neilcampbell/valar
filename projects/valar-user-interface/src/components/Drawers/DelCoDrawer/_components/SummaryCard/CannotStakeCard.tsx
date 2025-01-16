import { cn } from "@/lib/shadcn-utils";

const CannotStakeCard: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={cn("", className)}>
      <h1 className="my-1 font-bold">Not possible to select this node runner.</h1>
    </div>
  );
};

export default CannotStakeCard;
