"use client";
import { createContext, useContext } from "react";

export interface AppUser {
  id: string;
  email: string;
  token: string;
}

export interface OrgContext {
  org_id: string;
  org_name: string;
  role: string;
}

interface AppContextType {
  user: AppUser | null;
  org: OrgContext | null;
  setOrg: (org: OrgContext) => void;
}

export const AppContext = createContext<AppContextType>({
  user: null,
  org: null,
  setOrg: () => {},
});

export function useApp() {
  return useContext(AppContext);
}
