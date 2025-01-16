import { cn } from "@/lib/shadcn-utils";

const StatusCell = ({
  className,
  status,
}: {
  className?: string;
  status: string;
}) => {
  return (
    <div className="flex items-center gap-1">
      <div className={cn("h-2 w-2 rounded-full", className)} /> {status}
    </div>
  );
};

export default StatusCell;
