/**
 * This file is based on: https://github.com/algorandfoundation/reti/blob/212ae92777a64db76f7634c806c77414c09e4c49/ui/src/utils/network/getExplorerConfig.ts
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

export interface ExplorerConfig {
  accountUrl: string
  transactionUrl: string
  assetUrl: string
  appUrl: string
}

export function getExplorerConfigFromViteEnvironment(): ExplorerConfig {
  if (!import.meta.env.VITE_EXPLORER_ACCOUNT_URL) {
    throw new Error(
      'Attempt to get block explorer config without specifying VITE_EXPLORER_ACCOUNT_URL in the environment variables',
    )
  }

  return {
    accountUrl: import.meta.env.VITE_EXPLORER_ACCOUNT_URL,
    transactionUrl: import.meta.env.VITE_EXPLORER_TRANSACTION_URL,
    assetUrl: import.meta.env.VITE_EXPLORER_ASSET_URL,
    appUrl: import.meta.env.VITE_EXPLORER_APPLICATION_URL,
  }
}