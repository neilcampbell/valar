import { Container } from "@/components/Container/Container";
import { cn } from "@/lib/shadcn-utils";
import { useEffect, useState } from "react";

const AlphabetSet = new Set<string>([]);

const GlossaryList: { term: string; info: JSX.Element | string }[] = [
  {
    term: "Account",
    info: (
      <span>
        Also known as an address, is your public identifier on the blockchain.
        It fulfills a similar role in blockchain as your bank account or phone
        number do in traditional systems. The access rights to your accounts are
        stored in your wallet, but all the assets held at your accounts are
        stored on the blockchain.
      </span>
    ),
  },
  {
    term: "Address",
    info: (
      <span>
        A synonym for account.
      </span>
    ),
  },
  {
    term: "ALGO",
    info: (
      <span>
        The token of the Algorand blockchain network. It is used to secure the
        network by staking, to pay for the fees for its use, and in the
        network's governance.
      </span>
    ),
  },
  {
    term: "Algorand",
    info: (
      <span>
        A Pure Proof of Stake (PPoS) layer 1 blockchain.
      </span>
    ),
  },
  {
    term: "Algorand daemon",
    info: (
      <span>
        A computer program that is operating according to the Algorand protocol.
      </span>
    ),
  },
  {
    term: "Block",
    info: (
      <span>
        A group of transactions that happened since the last block was agreed in
        a blockchain network. A block serves as the time step in the blockchain
        network. It is also called a round. Each block is marked with a
        subsequent number.
      </span>
    ),
  },
  {
    term: "Blockchain",
    info: (
      <span>
        The technology that enables multiple people to agree on what has
        happened up to now and what is allowed to happen in the future, without
        them having to trust one another.
      </span>
    ),
  },
  {
    term: "Blockchain network",
    info: (
      <span>
        A particular implementation of the blockchain technology, for example
        Bitcoin, Ethereum, or Algorand.
      </span>
    ),
  },
  {
    term: "Consensus",
    info: <span>The process by which nodes in a distributed network agree on the validity of transactions and the state of the ledger.</span>,
  },
  {
    term: "Consensus participation",
    info: <span>A more technical term for staking.</span>,
  },
  {
    term: "Daemon",
    info: (
      <span>
        A computer program that is automatically responding and interacting with
        the blockchain.
      </span>
    ),
  },
  {
    term: "Delegator",
    info: (
      <span>
        A person or an entity that stakes their ALGO not by themselves.
      </span>
    ),
  },
  {
    term: "Hot wallet",
    info: (
      <span>
        A wallet that stores the keys for an account with low security concerns.
        For example, an account with a small amount of funds that is used for automating recurring transactions.
      </span>
    ),
  },
  {
    term: "Liquid staking",
    info: (
      <span>
        The act of sending one's funds to a third party's account for staking and receiving a token in exchange for the duration of the staking -- the token can typically be traded or exchanged for the initial stake plus part of the staking rewards.
      </span>
    ),
  },
  {
    term: "Network",
    info: (
      <span>A group of nodes that are all operating under the same rules.</span>
    ),
  },
  {
    term: "Node",
    info: (
      <span>
        A computer that is running a specific computer program 24 hours a day, 7
        days a week, 365 days a year.
      </span>
    ),
  },
  {
    term: "Node Runner",
    info: (
      <span>
        Also called a validator, is a person or an entity that is validating
        transactions and producing new blocks on the blockchain network.
      </span>
    ),
  },
  {
    term: "Participation Keys",
    info: (
      <span>
        A set of cryptographic private keys that are used solely for voting on
        and confirming the blocks of the blockchain network, i.e. for staking.
        These keys cannot be used to move any assets.
      </span>
    ),
  },
  {
    term: "Round",
    info: <span>Another name for a block in the blockchain network.</span>,
  },
  {
    term: "Spending Keys",
    info: (
      <span>
        Cryptographic private keys used to sign, i.e. authorize and approve, all
        trans- actions of a user on a blockchain.
      </span>
    ),
  },
  {
    term: "Staking",
    info: (
      <span>
        The process of securing the blockchain network by validating
        transactions and producing new blocks on the blockchain network.
      </span>
    ),
  },
  {
    term: "Stablecoin",
    info: (
      <span>
        A crypto asset pegged to a fiat currency like USD or EUR.
      </span>
    ),
  },
  {
    term: "Staking pool",
    info: (
      <span>
        A central account that accumulates funds from multiple accounts and stakes the accumulated funds.
      </span>
    ),
  },
  {
    term: "Staking rewards",
    info: (
      <span>
        Incentives that are give out by the network for participating in its consensus, i.e. staking.
      </span>
    ),
  },
  {
    term: "Transaction",
    info: (
      <span>
        Any action taken by a user of a blockchain network. Most commonly a
        payment but can be anything from a simple notification to a complex
        calculation.
      </span>
    ),
  },
  {
    term: "Valar",
    info: <span>Platform for peer-to-peer staking on Algorand.</span>,
  },
  {
    term: "Valar Daemon",
    info: (
      <span>
        A computer program for node runners that want to automatically service
        the staking requests of Algorand users made via Valar platform.
      </span>
    ),
  },
  {
    term: "Validator",
    info: (
      <span>
        Also called a node runner, is a person or an entity that is validating
        transactions and producing new blocks on the blockchain network. The
        role of the validator is similar to the role of a miner in Bitcoin.
      </span>
    ),
  },
  {
    term: "Wallet",
    info: (
      <span>
        A digital wallet that holds the spending keys of one or more of your
        blockchain accounts.
      </span>
    ),
  },
];

//Sorting Alphabetically and Filling Alphabet-Set
GlossaryList.sort((a, b) => a.term.localeCompare(b.term)).forEach((v) =>
  AlphabetSet.add(v.term.charAt(0)),
);

const GlossaryPage = () => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 42);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    const element = document.getElementsByClassName(id)[0];
    const topOffSet = window.innerWidth <= 648 ? 120 : 108;

    if (element) {
      const elementPosition = element.getBoundingClientRect().top;
      const scrollToY = window.scrollY + elementPosition - topOffSet;

      window.scrollTo({
        top: scrollToY,
        behavior: "smooth",
      });
    }
  };

  const scrollToEntry = (id: string) => {
    console.log(`Scrolling to ${id}`)
    const element = document.getElementById(id);
    const topOffSet = window.innerWidth <= 648 ? 120 : 108;

    console.log(element)

    if (element) {
      const elementPosition = element.getBoundingClientRect().top;
      const scrollToY = window.scrollY + elementPosition - topOffSet;

      window.scrollTo({
        top: scrollToY,
        behavior: "smooth",
      });

      window.history.pushState(null, "", `#${id}`);
    }
  };

  useEffect(() => {
    if (window.location.hash) {
      const id = window.location.hash.substring(1);
      scrollToEntry(id);
    }
  }, []);

  return (
    <Container className="px-0">
      <div className="lg:px-20 lg:py-4">
        <h1 className="px-2 text-3xl font-semibold">Glossary</h1>
        <div className="grid grid-cols-1 lg:mt-6 lg:grid-cols-4">
          <div
            className={cn(
              "sticky top-[72px] col-span-1 pt-2 z-0",
              isScrolled ? "bg-background lg:bg-transparent" : "bg-transparent",
            )}
          >
            <div className="flex gap-4 px-2 text-secondary lg:fixed lg:flex-col lg:gap-6">
              {Array.from(AlphabetSet).map((c, index) => (
                <h1
                  key={index}
                  className="cursor-pointer"
                  onClick={() => scrollToSection(`${c}_`)}
                >
                  {c}
                </h1>
              ))}
            </div>
          </div>
          <div className="col-span-3 px-2">
            <div className="mt-8 flex flex-col gap-6 lg:mt-0">
              {GlossaryList.map((section, index) => (
                <>
                  <div 
                    key={index}
                    className={`${section.term.charAt(0)}_`}
                    id={section.term.replace(/\s+/g, '-').toLowerCase()}
                  >
                    <h1 className="mb-1 font-semibold">{section.term}</h1>
                    <p className="leading-6">{section.info}</p>
                  </div>
                </>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Container>
  );
};

export default GlossaryPage;
