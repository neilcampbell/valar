import { Separator } from "@/components/ui/separator";

import ValAdDrawer from "@/components/Drawers/ValAdDrawer/ValAdDrawer";

const CreateAdCard = () => {

  return (
    <div className="rounded-lg border-border p-2 lg:border lg:bg-background-light">
      <h1 className="mb-2 font-bold">Create Node Runner Ad</h1>
      <Separator className="hidden bg-border lg:block" />
      <p className="mt-2 text-sm text-text-secondary">
        Create your ad and let Algorand users stake on your node.
      </p>
      <ValAdDrawer valAppId={undefined} />
    </div>
  );
};

export default CreateAdCard;
