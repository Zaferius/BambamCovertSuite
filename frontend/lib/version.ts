/**
 * Application Version — single source of truth is the root /VERSION file.
 * next.config.mjs reads that file and injects it as process.env.APP_VERSION.
 */
export const APP_VERSION = process.env.APP_VERSION ?? "1.5.1";
