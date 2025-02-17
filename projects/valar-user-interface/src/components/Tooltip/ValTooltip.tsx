import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/shadcn-utils";
import { NodeRelation } from "@/utils/staking-utils";
import { Star } from "lucide-react";

const tooltipMessages: Record<Exclude<NodeRelation, undefined>, string> = {
  "staking-you": "You are currently staking on this node. For details see ",
  "staking-others": "You are currently staking on this node with another account. For details see ",
  "awaiting-you": "This node is being prepared for you. To start staking, please confirm its setup. You can do this in ",
  "awaiting-others": "This node is being prepared for one of your accounts. To start staking, please confirm its setup. You can do this in ",
  "used": "You have staked on this node in the past. For details see ",
  "your-ad": "This is your ad. For details see ",
};

const iconClasses: Record<Exclude<NodeRelation, undefined>, string> = {
  "staking-you": "h-5 w-5 fill-current text-yellow-500",
  "staking-others": "h-5 w-5 fill-current text-yellow-500",
  "awaiting-you": "h-5 w-5 text-secondary",
  "awaiting-others": "h-5 w-5 text-secondary",
  "used": "h-5 w-5 text-yellow-500",
  "your-ad": "h-5 w-5 fill-current text-yellow-500",
};

const ValTooltip = ({ className, relation }: { className?: string; relation: NodeRelation }) => {
  if (!relation) return;

  return (
    <TooltipProvider delayDuration={5}>
      <Tooltip>
        <TooltipTrigger className="cursor-default">
          <Star className={cn(iconClasses[relation], className)} />
        </TooltipTrigger>
        <TooltipContent className="max-w-48">
          <p>
            {tooltipMessages[relation]}
            <a href="/dashboard" className="text-secondary">
              Dashboard
            </a>
            .
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default ValTooltip;