"use client";

import { useAuth } from "../lib/auth-context";
import { UserBotSettings } from "./user-bot-settings";

type Props = {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
};

export function UserSettingsPanel({ isOpen, setIsOpen }: Props) {
  const { user } = useAuth();

  return (
    <>
      <div
        className={`settings-panel-overlay ${isOpen ? "show" : ""}`}
        onClick={() => setIsOpen(false)}
      />

      <div className={`settings-panel-sidebar ${isOpen ? "open" : ""}`}>
        <div className="admin-panel-header">
          <h3>⚙️ Settings</h3>
          <button
            className="admin-panel-close"
            onClick={() => setIsOpen(false)}
            title="Close"
          >
            ✕
          </button>
        </div>

        <div className="admin-panel-content">
          <div className="admin-section">
            <h4>Account</h4>
            <p style={{ color: "var(--muted)", marginBottom: "8px" }}>
              <strong>{user?.username}</strong>{" "}
              {user?.is_admin && <span style={{ marginLeft: "6px" }}>👑 Admin</span>}
            </p>
          </div>

          <div className="admin-section">
            <UserBotSettings />
          </div>
        </div>
      </div>
    </>
  );
}
