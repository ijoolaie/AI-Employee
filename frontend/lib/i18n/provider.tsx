"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { messages, type Locale } from "./messages";

type TranslationMessages = (typeof messages)[Locale];

type I18nContext = { locale: Locale; setLocale: (locale: Locale) => void; t: TranslationMessages; dir: "ltr" | "rtl" };

const Context = createContext<I18nContext | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    const saved = window.localStorage.getItem("aiep.locale");
    if (saved === "fa" || saved === "en") setLocaleState(saved);
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === "fa" ? "rtl" : "ltr";
    document.documentElement.dataset.locale = locale;
    window.localStorage.setItem("aiep.locale", locale);
  }, [locale]);

  const value = useMemo(() => {
    const dir: "ltr" | "rtl" = locale === "fa" ? "rtl" : "ltr";
    return {
      locale,
      setLocale: (next: Locale) => setLocaleState(next),
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
