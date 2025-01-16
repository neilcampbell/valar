

import { TERMS_AND_CONDITIONS } from "@/constants/terms-and-conditions";
import LinkExt from "../ui/link-ext";
import { cn } from "@/lib/shadcn-utils";
import { emailLink } from "@/constants/socials";

const TermsAndConditions: React.FC<{
  terms: string
  className?: string
}> = ({
  terms,
  className,
}) => {

  let href = TERMS_AND_CONDITIONS.get(terms);
  let text = "Terms & Conditions";

  if(!href){
    href = emailLink;
    text = "Unknown Terms & Conditions - notify developers";
  }

  return (
    <LinkExt
      href={href}
      text={text}
      className={cn("text-secondary", className)}
    />
  );
}
export default TermsAndConditions;
