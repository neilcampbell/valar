import Logo from "@/assets/logo/full-logo.svg?react";
import discord from "@/assets/socials/discord.svg";
import github from "@/assets/socials/github.svg";
import linkedIn from "@/assets/socials/linkedin.svg";
import telegram from "@/assets/socials/telegram.svg";
import x from "@/assets/socials/twitter.svg";
import { Container } from "@/components/Container/Container";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Wallet } from "@/components/Wallet/Wallet";
import {
  discordLink,
  githubLink,
  linkedInLink,
  telegramLink,
  twitterLink,
} from "@/constants/socials";
import useMobileMenuStore from "@/store/mobileMenuStore";
import clsx from "clsx";
import { Ellipsis, Menu, X } from "lucide-react";
import { ReactNode, useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";

import MobileMenu from "./MobileMenu";
import { ParamsCache } from "@/utils/paramsCache";
import { FROM_BASE_TO_MILLI_MULTIPLIER } from "@/constants/units";

const socials = [
  {
    icon: x,
    label: "Twitter (X)",
    link: twitterLink,
  },
  {
    icon: telegram,
    label: "Telegram",
    link: telegramLink,
  },
  {
    icon: discord,
    label: "Discord",
    link: discordLink,
  },
  {
    icon: github,
    label: "Github",
    link: githubLink,
  },
  {
    icon: linkedIn,
    label: "LinkedIn",
    link: linkedInLink,
  },
];

const NavItem = ({ children, to }: { children: ReactNode; to: string }) => {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        isActive ? "text-sm font-semibold" : "text-sm font-semibold opacity-50"
      }
    >
      {children}
    </NavLink>
  );
};

export const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const { mobileMenuOpen, setMobileMenuOpen } = useMobileMenuStore();

  // -----------------------------------
  const showRounds = import.meta.env.VITE_ALGOD_NETWORK == "localnet" || import.meta.env.VITE_ENVIRONMENT != "production";
  const [round, setRound] = useState<bigint>(0n);
  const intervalTime = 1*FROM_BASE_TO_MILLI_MULTIPLIER; // refresh interval [ms]
  const getRound = async () => {
    if(showRounds){
      try {
        const round = await ParamsCache.getRound();
        setRound(round);
      } catch (error) {
        console.error('Error fetching round: ', error);
      }
    }
  };
  useEffect(() => {
    getRound();

    const interval = setInterval(() => {
      getRound();
    }, intervalTime);

    return () => clearInterval(interval);
  }, []);
  // -----------------------------------

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 0);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <div
        className={clsx(
          "fixed left-0 right-0 top-0 z-50 transition-colors duration-300",
          mobileMenuOpen ? "transition-none" : "transition-colors",
          isScrolled || mobileMenuOpen ? "bg-background" : "bg-transparent",
        )}
      >
        <Container>
          <div className="flex h-[72px] items-center justify-between py-4">
            <Link to="/">
              <Logo className="ml-3 h-6 lg:ml-0 lg:h-9" />
            </Link>

            <div className="hidden items-center gap-8 lg:flex">
              <NavItem to="/stake">Stake</NavItem>
              <NavItem to="/dashboard">Dashboard</NavItem>
              <NavItem to="/faq">FAQ</NavItem>
              <Popover>
                <PopoverTrigger>
                  <Ellipsis />
                </PopoverTrigger>
                <PopoverContent className="w-auto border-border bg-background p-1">
                  {socials.map((item, index) => (
                    <a
                      key={index}
                      className="flex items-center gap-2 rounded-md px-3 py-3 hover:bg-background-light"
                      href={item.link}
                      target="blank_"
                    >
                      <img src={item.icon} />{" "}
                      <p className="text-white">{item.label}</p>
                    </a>
                  ))}
                </PopoverContent>
              </Popover>
            </div>
            <div className="flex items-center gap-2">
              {showRounds && <div className="text-text-tertiary text-sm px-4">{"Current round: " + round}</div>}
              {!mobileMenuOpen && <Wallet />}
              <div
                className="block cursor-pointer lg:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X /> : <Menu />}
              </div>
            </div>
          </div>
        </Container>
        <MobileMenu socials={socials} />
      </div>
      <div id="navbar-spacer" className="h-[72px]" />
    </>
  );
};
