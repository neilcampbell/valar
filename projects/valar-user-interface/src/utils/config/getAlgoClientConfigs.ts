/**
 * This file is based on: https://github.com/algorandfoundation/reti/blob/31c306d71b9e04168be717507531b83f0006140f/ui/src/utils/network/getAlgoClientConfigs.ts
 * which is licensed based on the following license:
 * 
 * MIT License
 * 
 * Copyright (c) 2024 Algorand Foundation
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 * 
 * 
 * Changes to this code are licensed under the same conditions as the rest of this project.
 */

import { NetworkId } from '@txnlab/use-wallet-react'
import { AlgoViteClientConfig, AlgoViteKMDConfig } from '@/interfaces/network'

export function getAlgodConfigFromViteEnvironment(): AlgoViteClientConfig {
  if (!import.meta.env.VITE_ALGOD_SERVER) {
    throw new Error(
      'Attempt to get default algod configuration without specifying VITE_ALGOD_SERVER in the environment variables',
    )
  }

  return {
    server: import.meta.env.VITE_ALGOD_SERVER,
    port: import.meta.env.VITE_ALGOD_PORT,
    token: import.meta.env.VITE_ALGOD_TOKEN,
    network: import.meta.env.VITE_ALGOD_NETWORK,
  }
}

export function getIndexerConfigFromViteEnvironment(): AlgoViteClientConfig {
  if (!import.meta.env.VITE_INDEXER_SERVER) {
    throw new Error(
      'Attempt to get default algod configuration without specifying VITE_INDEXER_SERVER in the environment variables',
    )
  }

  return {
    server: import.meta.env.VITE_INDEXER_SERVER,
    port: import.meta.env.VITE_INDEXER_PORT,
    token: import.meta.env.VITE_INDEXER_TOKEN,
    network: import.meta.env.VITE_ALGOD_NETWORK,
  }
}

export function getKmdConfigFromViteEnvironment(): AlgoViteKMDConfig {
  if (!import.meta.env.VITE_KMD_SERVER) {
    throw new Error(
      'Attempt to get default kmd configuration without specifying VITE_KMD_SERVER in the environment variables',
    )
  }

  return {
    server: import.meta.env.VITE_KMD_SERVER,
    port: import.meta.env.VITE_KMD_PORT,
    token: import.meta.env.VITE_KMD_TOKEN,
    wallet: import.meta.env.VITE_KMD_WALLET,
    password: import.meta.env.VITE_KMD_PASSWORD,
  }
}

export function getAlgodNetwork(): NetworkId {
  const config = getAlgodConfigFromViteEnvironment()

  switch (config.network) {
    case 'mainnet':
      return NetworkId.MAINNET
    case 'testnet':
      return NetworkId.TESTNET
    case 'betanet':
      return NetworkId.BETANET
    case 'fnet':
      return NetworkId.FNET
    case 'localnet':
      return NetworkId.LOCALNET
    default:
      throw new Error(`Unknown network: ${config.network}`)
  }
}