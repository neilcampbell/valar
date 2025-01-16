# Valar User Interface

This project contains the user interface (UI) for [Valar](https://stake.valar.solutions) - a decentralized platform for connecting blockchain stakeholders (i.e. `Delegators`) to node runners (i.e. `Validators`) that offer direct participation in blockchain consensus, i.e. staking.
The UI contained in this project is an optional component of the Valar Platform.
It provides a more convenient access to the Valar Platform by enabling Validators to publish and manage their advertisements as well as the Delegators to start and manage their service contracts.The interactions with the Valar Platform can be done also without the use of this UI by interacting with the blockchain through any other means.

## Setup

### 1. Clone the Repository
Start by cloning this repository to your local machine.

### 2. Install Pre-requisites
Ensure the following pre-requisites are installed and properly configured:

- **npm**: Node package manager. Install from [Node.js Installation Guide](https://nodejs.org/en/download/). Verify with `npm -v` to see version `18.12`+.
- **AlgoKit CLI**: Essential for project setup and operations. Install the latest version from [AlgoKit CLI Installation Guide](https://github.com/algorandfoundation/algokit-cli#install). Verify installation with `algokit --version`, expecting `2.5.1` or later.

### 3. Bootstrap Your Local Environment
Run the following commands within the project folder:

- **Install project dependencies**: with `algokit project bootstrap all`

- **Start development server**: with `npm run dev`

> Please note, by default the frontend is pre-configured to run against Algorand LocalNet. If you want to run against FNet, TestNet, or MainNet, comment out the current environment variable and uncomment the relevant one in [`.env`](.env) file that is created after running bootstrap command and based on [`.env.template`](.env.template).

## Tools

This project makes use of React and Tailwind to provider a base project configuration to develop frontends for Algorand dApps and interactions with smart contracts. The following tools are in use:

- [AlgoKit Utils](https://github.com/algorandfoundation/algokit-utils-ts) - Various TypeScript utilities to simplify interactions with Algorand and AlgoKit.
- [React](https://reactjs.org/) - A JavaScript library for building user interfaces.
- [Tailwind CSS](https://tailwindcss.com/) - A utility-first CSS framework for rapidly building custom designs.
- [daisyUI](https://daisyui.com/) - A component library for Tailwind CSS.
- [use-wallet](https://github.com/txnlab/use-wallet) - A React hook for connecting to an Algorand wallet providers.
- [npm](https://www.npmjs.com/): Node.js package manager
- [jest](https://jestjs.io/): JavaScript testing framework
- [playwright](https://playwright.dev/): Browser automation library
- [Prettier](https://prettier.io/): Opinionated code formatter
- [ESLint](https://eslint.org/): Tool for identifying and reporting on patterns in JavaScript

