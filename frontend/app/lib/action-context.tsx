"use client";

import { createContext, useContext, useState, ReactNode } from "react";

type ActionContextType = {
  action: string;
  setAction: (action: string) => void;
};

const ActionContext = createContext<ActionContextType | null>(null);

export function ActionProvider({ children }: { children: ReactNode }) {
  const [action, setAction] = useState("idle");

  return (
    <ActionContext.Provider value={{ action, setAction }}>
      {children}
    </ActionContext.Provider>
  );
}

export function useAction() {
  const context = useContext(ActionContext);
  if (!context) {
    throw new Error("useAction must be used within an ActionProvider");
  }
  return context;
}
