import configLocalnet from '../../constants/platform.localnet.json'
import configFnet from '../../constants/platform.fnet.json'

// Select platform configuration depending on the network
export function getPlatformConfig() {
  if (!import.meta.env.VITE_ALGOD_NETWORK) {
    throw new Error(
      'Attempt to get algod config without specifying VITE_ALGOD_NETWORK in the environment variables',
    )
  }

  let config;
  switch (import.meta.env.VITE_ALGOD_NETWORK) {
    case "localnet":
      config = configLocalnet;
      break;
    case "fnet":
        config = configFnet;
        break;
    default:
      throw("Unexpected network.");
      break;
  }

  return config;
}
