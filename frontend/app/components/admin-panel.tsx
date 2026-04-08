"use client";

import { useEffect, useState, useMemo } from "react";
import { authFetch } from "../lib/auth-fetch";

type ActiveUser = {
  username: string;
  is_admin: boolean;
  action: string;
  last_seen: number;
};

export function AdminPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    []
  );

  useEffect(() => {
    if (!isOpen) return;

    const fetchUsers = async () => {
      try {
        const res = await authFetch(`${apiBaseUrl}/auth/online-users`);
        if (res.ok) {
          const data = await res.json();
          setActiveUsers(data);
        }
      } catch (err) {}
    };

    fetchUsers();
    const interval = setInterval(fetchUsers, 3000);
    return () => clearInterval(interval);
  }, [isOpen, apiBaseUrl]);

  return (
    <div className="admin-panel-wrapper">
      <button 
        className="admin-panel-toggle" 
        onClick={() => setIsOpen(!isOpen)}
        title="Admin Panel: Active Users"
      >
        <span style={{ fontSize: "16px" }}>👥</span> 
        Admin Panel
      </button>

      {isOpen && (
        <div className="admin-panel-dropdown">
          <div className="admin-panel-header">
            <h4>Active Users</h4>
          </div>
          {activeUsers.length === 0 ? (
            <p className="admin-empty">No active users</p>
          ) : (
            <ul className="admin-user-list">
              {activeUsers.map((u) => {
                const isIdle = u.action === "idle";
                return (
                  <li key={u.username} className="admin-user-item">
                    <div className="admin-user-info">
                      <span className="admin-user-name">
                        {u.username} {u.is_admin ? "👑" : ""}
                      </span>
                      <div className={`status-dot ${isIdle ? "dot-idle" : "dot-active"}`} />
                    </div>
                    <span className="admin-user-action">
                      {isIdle ? "Idle" : `Processing: ${u.action}`}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
