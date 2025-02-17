import Axios from 'axios'
import { setupCache } from 'axios-cache-interceptor'
import queryString from 'query-string'
import { getNfdApiFromViteEnvironment } from '@/utils/config/getNfdConfig'
import { getGoveranceApiConfig } from '@/utils/config/getGovernanceApiConfig'

const instance = Axios.create({
  baseURL: getNfdApiFromViteEnvironment(),
  paramsSerializer: (params) => queryString.stringify(params),
})
const axios = setupCache(instance)

export const governanceAxios = Axios.create({
  baseURL: getGoveranceApiConfig(),
});

export default axios;