import { cn } from "@/lib/shadcn-utils";
import * as React from "react";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-9 w-full rounded-md border border-neutral-200 bg-transparent px-3 py-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-neutral-950 placeholder:text-neutral-500 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-neutral-950 disabled:cursor-not-allowed disabled:opacity-50 dark:border-neutral-800 dark:file:text-neutral-50 dark:placeholder:text-neutral-400 dark:focus-visible:ring-neutral-300 md:text-sm",
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";

const InputUnit = React.forwardRef<
  HTMLInputElement,
  React.ComponentProps<"input"> & { unit: React.ReactNode; unitClassName?: string }
>(({ className, unit, unitClassName, ...props }, ref) => {
  const { disabled } = props;
  return (
    <div
      className={cn(
        "flex h-9 items-center gap-1 rounded-md border border-neutral-200 bg-transparent px-1 py-1 focus-visible:ring-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-neutral-950 placeholder:text-neutral-500 focus-visible:outline-none  focus-visible:ring-neutral-950 disabled:cursor-not-allowed disabled:opacity-50 dark:border-neutral-800 dark:file:text-neutral-50 dark:placeholder:text-neutral-400 dark:focus-visible:ring-neutral-300 md:text-sm",
        className,
        disabled && "border-opacity-50",
      )}
    >
      <input
        className="ml-2 w-full min-w-9 flex-1 appearance-none border-0 border-neutral-200 bg-transparent px-0 py-0 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-neutral-950 placeholder:text-neutral-500 focus-visible:outline-none focus-visible:ring-0 focus-visible:ring-neutral-950 disabled:cursor-not-allowed disabled:opacity-50 dark:border-neutral-800 dark:file:text-neutral-50 dark:placeholder:text-neutral-400 dark:focus-visible:ring-neutral-300 md:text-sm [&::-webkit-inner-spin-button]:hidden [&::-webkit-outer-spin-button]:hidden"
        ref={ref}
        {...props}
      />
      <div className={cn("mr-1 text-right", unitClassName, disabled && "opacity-50")}>
        {unit}
      </div>
    </div>
  );
});

export { Input, InputUnit };
