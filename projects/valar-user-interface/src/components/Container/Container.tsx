import { cn } from "@/lib/shadcn-utils";

export const Container = ({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) => {
  return (
    <div className={cn("flex w-full px-2 lg:px-12", className)}>
      <div className="container mx-auto 2xl:max-w-screen-xl">{children}</div>
    </div>
  );
};
