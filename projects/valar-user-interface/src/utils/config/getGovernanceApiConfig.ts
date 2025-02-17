export function getGoveranceApiConfig() {
  if (import.meta.env.VITE_ENVIRONMENT === "local") {
    return "/gov";
  }

  return import.meta.env.VITE_GOVERNANCE_URL ?? "";
}