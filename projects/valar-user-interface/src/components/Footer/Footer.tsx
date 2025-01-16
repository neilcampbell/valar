import Logo from "@/assets/logo/full-logo.svg?react";
import { Link } from "react-router-dom";

import { Container } from "../Container/Container";
import { TC_LATEST, TERMS_AND_CONDITIONS } from "@/constants/terms-and-conditions";
import LinkExt from "../ui/link-ext";

const Footer = () => {
  return (
    <>
      <div
        id="footer"
        className="w-full border-t-[0.8px] border-gray-600 py-[16px]"
      >
        <Container>
          <div className="flex items-center justify-between">
            <div className="flex flex-col items-center gap-[4px]">
              <Link to="/">
                <Logo className="h-[26px]" />
              </Link>
              <p className="text-xs font-medium">Valar App v0.0.1</p>
            </div>
            <div className="flex gap-4 lg:gap-9">
              <Link to="/glossary">
                <h1 className="text-sm text-gray-400">Glossary</h1>
              </Link>
              <h1 className="text-sm text-gray-400"><LinkExt href={TERMS_AND_CONDITIONS.get(TC_LATEST)!} text={"Terms of Use"}/></h1>
              <h1 className="text-sm text-gray-400"><LinkExt href={"https://valar.solutions"} text={"Valar Solutions"}/></h1>
            </div>
          </div>
        </Container>
      </div>
    </>
  );
};

export default Footer;
