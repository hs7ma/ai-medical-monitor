"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { I18nProvider } from "@/i18n/context";
import { useAuth } from "@/lib/auth";
import { Navbar } from "@/components/layout/Navbar";
import { ToastProvider } from "@/components/ui/Toast";
import { ModalProvider } from "@/components/ui/Modal";

function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, loadFromStorage } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    loadFromStorage();
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (!token && typeof window !== "undefined" && window.location.pathname !== "/login") {
      router.push("/login");
    }
  }, [router, token, mounted]);

  return (
    <div className="min-h-screen bg-med-bg">
      {mounted && token && <Navbar />}
      <main className={mounted && token ? "mx-auto max-w-[1600px] px-4 py-6 sm:px-6 sm:py-8" : ""}>
        {children}
      </main>
    </div>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <ToastProvider>
        <ModalProvider>
          <AppShell>{children}</AppShell>
        </ModalProvider>
      </ToastProvider>
    </I18nProvider>
  );
}
