import { Button } from "@/components/ui/button";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";
import { ScrollArea } from "@/components/ui/scroll-area";
import { X } from "lucide-react";
import { StakeReqs } from "@/lib/types";
import Contents from "./_components/Contents";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const DelCoDrawer = ({
  delAppId,
  valAppId,
  stakeReqs,
  possible,
}: {
  delAppId?: bigint;
  valAppId?: bigint;
  stakeReqs?: StakeReqs;
  possible?: boolean;
}) => {
  const [open, onOpenChange] = useState<boolean | undefined>(undefined);
  const [mount, setMount] = useState<boolean>(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (open == false && mount==false && !location.pathname.startsWith("/stake")) {
      navigate(0);
    }
    setMount(false)
  }, [open]);

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerTrigger asChild>
        {!delAppId ? (
          <Button variant={possible ? "v_primary" : "v_outline"} className="w-full">
            {possible ? "Stake" : "View"}
          </Button>
        ):(
          <div>
            <Button className="hidden lg:block" variant={"v_link"}>
              Details
            </Button>
            <Button className="text-xs lg:hidden" variant={"v_outline"}>
              Details
            </Button>
          </div>
        )}
      </DrawerTrigger>
      <DrawerContent className="h-[90%] lg:h-[calc(100vh-72px)] md:h-[calc(100vh-48px)] rounded-t-3xl border-t border-border bg-background pb-3 pt-12 lg:pt-9">
        <DrawerTitle />
        <DrawerDescription />
        <ScrollArea>
          <Contents
            delAppId={delAppId}
            valAppId={valAppId}
            stakeReqs={stakeReqs}
            open={open}
            onOpenChange={onOpenChange}
          />
        </ScrollArea>
        <DrawerClose className="absolute right-4 top-3 lg:top-4">
          <X />
        </DrawerClose>
      </DrawerContent>
    </Drawer>
  );
};

export default DelCoDrawer;
