import useMobileMenuStore from "@/store/mobileMenuStore";
import clsx from "clsx";
import { ReactNode, useEffect } from "react";
import { NavLink, To } from "react-router-dom";

import { Container } from "../Container/Container";

const MenuItem = ({ children, to }: { children: ReactNode; to: To }) => {
  const { setMobileMenuOpen } = useMobileMenuStore();
  return (
    <NavLink
      to={to}
      className={({ isActive }) => (isActive ? "opacity-100" : "opacity-50")}
      onClick={() => setMobileMenuOpen(false)}
    >
      <div className="h-9 px-3 py-2 text-sm font-medium hover:bg-background-light">
        {children}
      </div>
    </NavLink>
  );
};

const MobileMenu = ({
  socials,
}: {
  socials: {
    icon: any;
    label: string;
    link: string;
  }[];
}) => {
  const { mobileMenuOpen } = useMobileMenuStore();

  return (
    <div
      className={clsx(
        "flex flex-col gap-2 overflow-hidden border-border bg-background",
        mobileMenuOpen ? "h-full border-y px-1 pt-2" : "h-0 border-y-0 p-0",
      )}
    >
      <Container>
        <MenuItem to={"/stake"}>Stake</MenuItem>
        <MenuItem to={"/dashboard"}>Dashboard</MenuItem>
        <MenuItem to={"/faq"}>FAQ</MenuItem>
      </Container>
      <div className="flex justify-evenly border-t border-border py-3">
        {socials.map((item, index) => (
          <a key={index} href={item.link} target="blank_">
            <img src={item.icon} />
          </a>
        ))}
      </div>
    </div>
  );
};

export default MobileMenu;
