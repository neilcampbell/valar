import { cn } from "@/lib/shadcn-utils";
import { ReactNode } from "react";

export const InfoSection: React.FC<{
  className?: string;
  children: ReactNode;
}> = ({ className, children }) => {
  return <div className={cn("flex flex-col gap-1", className)}>{children}</div>;
};

export const InfoHeading: React.FC<{
  className?: string;
  children: ReactNode;
}> = ({ className, children }) => {
  return <div className={cn("font-semibold", className)}>{children}</div>;
};

export const InfoItem: React.FC<{
  className?: string;
  children: ReactNode;
}> = ({ className, children }) => {
  return (
    <div className={cn("flex flex-wrap gap-1", className)}>{children}</div>
  );
};

export const InfoLabel: React.FC<{
  className?: string;
  children: ReactNode;
}> = ({ className, children }) => {
  return (
    <div
      className={cn("items-center gap-1 text-sm text-text-tertiary", className)}
    >
      {children}
    </div>
  );
};

export const InfoValue: React.FC<{
  className?: string;
  children: ReactNode;
}> = ({ className, children }) => {
  return <div className={cn("text-sm text-text break-all", className)}>{children}</div>;
};
