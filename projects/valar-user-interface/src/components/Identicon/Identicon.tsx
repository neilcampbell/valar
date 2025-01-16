import { cn } from "@/lib/shadcn-utils";
import CryptoJS from "crypto-js";
import Identicon from "identicon.js";

const IdenticonAvatar = ({
  value,
  className,
}: {
  value: string;
  className?: string;
}) => {
  // Generate a hash for the input value (e.g., username)
  const hash = CryptoJS.MD5(value).toString();

  // Generate the identicon as a base64 PNG
  const data = new Identicon(hash, 100).toString();

  // Create a data URL for the image
  const src = `data:image/png;base64,${data}`;

  return (
    <img src={src} alt="Identicon" className={cn("rounded-full w-7 h-7", className)} />
  );
};

export default IdenticonAvatar;
