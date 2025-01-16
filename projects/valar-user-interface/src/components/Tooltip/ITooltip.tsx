import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/shadcn-utils";
import { Info } from "lucide-react";
import { ReactNode } from "react";

const ITooltip = ({
  className,
  value,
}: {
  className?: string;
  value?: ReactNode;
}) => {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Info className={cn("inline h-4 w-4", className)} />
        </TooltipTrigger>
        <TooltipContent className="max-w-48">{value}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default ITooltip;
