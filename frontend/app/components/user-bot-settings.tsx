"use client";

import { useEffect, useState, useMemo } from "react";
import { authFetch } from "../lib/auth-fetch";

export function UserBotSettings() {
  const [botToken, setBotToken] = useState("");
  const [botEnabled, setBotEnabled] = useState(false);
  const [botHasToken, setBotHasToken] = useState(false);
  const [botSaveLoading, setBotSaveLoading] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    []
  );

  useEffect(() => {
    const fetchBotSettings = async () => {
      try {
        const res = await authFetch(`${apiBaseUrl}/auth/user/bot-settings`);
        if (res.ok) {
          const data = (await res.json()) as any;
          setBotEnabled(data.bot_enabled ?? false);
          setBotHasToken(data.has_token ?? false);
          setBotToken("");
        }
      } catch (err) {}
    };

    void fetchBotSettings();
  }, [apiBaseUrl]);

  const handleSaveBotSettings = async () => {
    setBotSaveLoading(true);
    setSaveMessage("");
    try {
      const payload: any = { bot_enabled: botEnabled };
      if (botToken.trim()) {
        payload.telegram_bot_token = botToken;
      }

      const res = await authFetch(`${apiBaseUrl}/auth/user/bot-settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const result = await res.json();
        setBotToken("");
        setBotHasToken(result.has_token);
        setBotEnabled(result.bot_enabled);
        setSaveMessage("✓ Bot settings saved successfully!");
        setTimeout(() => setSaveMessage(""), 3000);
      } else {
        setSaveMessage("✗ Failed to save bot settings");
      }
    } catch (err) {
      setSaveMessage("✗ Error saving bot settings");
    } finally {
      setBotSaveLoading(false);
    }
  };

  return (
    <div className="converter-form">
      <h2 style={{ marginBottom: "20px" }}>🤖 Telegram Bot Settings</h2>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div className="field-group">
          <span>Bot Configuration</span>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
            <div style={{ fontSize: "0.9rem", color: "var(--muted)" }}>
              <p>Status: {botEnabled ? "✓ Enabled" : "✗ Disabled"}</p>
              <p>Token: {botHasToken ? "✓ Configured" : "✗ Not configured"}</p>
            </div>
          </div>
        </div>

        <div className="field-group">
          <span>Telegram Bot Token</span>
          <input
            type="password"
            placeholder="Paste your Telegram bot token from @BotFather"
            value={botToken}
            onChange={(e) => setBotToken(e.target.value)}
            style={{
              width: "100%",
              padding: "12px 14px",
            }}
          />
          <p style={{ fontSize: "0.75rem", marginTop: 4, color: "var(--muted)" }}>
            Leave empty to keep your current token. Get a token from @BotFather on Telegram.
          </p>
        </div>

        <div className="checkbox-group">
          <input
            type="checkbox"
            id="bot-enabled"
            checked={botEnabled}
            onChange={(e) => setBotEnabled(e.target.checked)}
          />
          <label htmlFor="bot-enabled" style={{ cursor: "pointer", margin: 0 }}>
            Enable my Telegram bot
          </label>
        </div>

        <button
          className="primary-button"
          onClick={() => void handleSaveBotSettings()}
          disabled={botSaveLoading}
          style={{
            padding: "12px 24px",
            fontSize: "0.95rem",
            opacity: botSaveLoading ? 0.5 : 1,
            cursor: botSaveLoading ? "not-allowed" : "pointer",
            width: "fit-content",
          }}
        >
          {botSaveLoading ? "Saving..." : "Save Bot Settings"}
        </button>

        {saveMessage && (
          <div
            style={{
              padding: "12px",
              borderRadius: "8px",
              backgroundColor: saveMessage.includes("✓") ? "rgba(0, 200, 100, 0.1)" : "rgba(248, 113, 113, 0.1)",
              color: saveMessage.includes("✓") ? "#00e87a" : "#f87171",
              fontSize: "0.9rem",
            }}
          >
            {saveMessage}
          </div>
        )}

        <div
          style={{
            marginTop: 16,
            padding: 16,
            borderRadius: "12px",
            border: "1px solid var(--border)",
            background: "rgba(28, 10, 42, 0.5)",
          }}
        >
          <h3 style={{ marginTop: 0, marginBottom: 8, fontSize: "1rem" }}>How to set up your bot:</h3>
          <ol style={{ margin: 0, paddingLeft: "20px", color: "var(--muted)", fontSize: "0.9rem", lineHeight: 1.6 }}>
            <li>Open Telegram and message @BotFather</li>
            <li>Send /newbot and follow the prompts</li>
            <li>Copy your bot token</li>
            <li>Paste it above and enable your bot</li>
            <li>Search for your bot on Telegram and send /start</li>
            <li>Send any file (image, audio, video, document) to test</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
