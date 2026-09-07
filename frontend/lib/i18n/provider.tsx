"use client";

import { createContext, useContext, useEffect, useMemo, useSyncExternalStore, type ReactNode } from "react";
import { messages, type Locale } from "./messages";

type TranslationMessages = (typeof messages)[Locale];

type I18nContext = { locale: Locale; setLocale: (locale: Locale) => void; t: TranslationMessages; dir: "ltr" | "rtl" };

const Context = createContext<I18nContext | null>(null);
const LOCALE_STORAGE_EVENT = "aiep-locale-change";
function subscribeLocale(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(LOCALE_STORAGE_EVENT, callback);
  return () => { window.removeEventListener("storage", callback); window.removeEventListener(LOCALE_STORAGE_EVENT, callback); };
}
function getLocaleSnapshot(): Locale {
  if (typeof window === "undefined") return "en";
  return window.localStorage.getItem("aiep.locale") === "fa" ? "fa" : "en";
}
function getServerLocaleSnapshot(): Locale { return "en"; }

export function I18nProvider({ children }: { children: ReactNode }) {
  const locale = useSyncExternalStore(subscribeLocale, getLocaleSnapshot, getServerLocaleSnapshot);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === "fa" ? "rtl" : "ltr";
    document.documentElement.dataset.locale = locale;
  }, [locale]);

  const value = useMemo(() => {
    const dir: "ltr" | "rtl" = locale === "fa" ? "rtl" : "ltr";
    return {
      locale,
      setLocale: (next: Locale) => {
        window.localStorage.setItem("aiep.locale", next);
        window.dispatchEvent(new Event(LOCALE_STORAGE_EVENT));
      },
      t: messages[locale],
      dir,
    };
  }, [locale]);

  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useI18n() {
  const value = useContext(Context);
  if (!value) throw new Error("useI18n must be used inside I18nProvider");
  return value;
}
