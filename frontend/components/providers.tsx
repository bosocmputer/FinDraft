"use client";
import { useState, useEffect, ReactNode } from "react";
import { AppContext, AppUser, OrgContext } from "@/lib/store";
import { supabase } from "@/lib/auth";
import { Toaster } from "sonner";

export function Providers({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null);
  const [org, setOrg] = useState<OrgContext | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        setUser({
          id: data.session.user.id,
          email: data.session.user.email!,
          token: data.session.access_token,
        });
      }
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setUser({
          id: session.user.id,
          email: session.user.email!,
          token: session.access_token,
        });
      } else {
        setUser(null);
        setOrg(null);
      }
    });

    return () => listener.subscription.unsubscribe();
  }, []);

  // Restore org from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("findraft_org");
    if (saved) setOrg(JSON.parse(saved));
  }, []);

  const handleSetOrg = (o: OrgContext) => {
    setOrg(o);
    localStorage.setItem("findraft_org", JSON.stringify(o));
  };

  return (
    <AppContext.Provider value={{ user, org, setOrg: handleSetOrg }}>
      <Toaster richColors position="top-right" />
      {children}
    </AppContext.Provider>
  );
}
