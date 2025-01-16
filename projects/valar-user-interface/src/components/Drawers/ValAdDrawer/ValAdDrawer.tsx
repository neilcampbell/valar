import { Container } from "@/components/Container/Container";
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
import { Separator } from "@/components/ui/separator";
import { X } from "lucide-react";

import Contents from "./_components/Contents";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const ValAdDrawer = ({
  valAppId,
}: {
  valAppId?: bigint;
}) => {
  const [open, setOpen] = useState<boolean>(false);
  const [mount, setMount] = useState<boolean>(true)
  const navigate = useNavigate();

  useEffect(() => {
    if (open == false && mount==false) {
      navigate(0);
    }
    setMount(false)
  }, [open]);

  return (
    <Drawer open={open} onOpenChange={setOpen}>
      <DrawerTrigger asChild>
        {!valAppId ? (
          <Button variant={"v_primary"} className="mt-3 w-full">
            Create Ad
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
      <DrawerContent className="h-[90%] lg:h-[calc(100vh-72px)] md:h-[calc(100vh-48px)] rounded-t-3xl border-t border-border bg-background pb-10 pt-9 lg:pt-6">
        <ScrollArea>
          <Container className="lg:px-4">
            <div className="space-y-1">
              <DrawerTitle className="font-bold">{!valAppId ? "Creating Ad" : "Ad Details"}</DrawerTitle>
              <DrawerDescription className="text-sm text-text">
                {!valAppId ? 
                  "Create an ad for your node by defining below your service terms and then publishing the ad." 
                : 
                  "Inspect or edit your ad details and monitor its performance."
                }
              </DrawerDescription>
            </div>
            <Separator className="mb-4 mt-2 bg-opacity-40" />
            <Contents valAppId={valAppId} onOpenChangeDrawer={() => setOpen(!open)} />
          </Container>
        </ScrollArea>
        <DrawerClose className="absolute right-4 top-3 lg:top-4">
          <X />
        </DrawerClose>
      </DrawerContent>
    </Drawer>
  );
};

export default ValAdDrawer;
