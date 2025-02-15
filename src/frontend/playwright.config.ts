import { defineConfig } from '@playwright/test';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config({ path: './src/frontend/.env' });

const FRONTEND_APP_URL = process.env.FRONTEND_APP_URL;
const PORT = process.env.NEXT_PUBLIC_PORT;

export default defineConfig({
  webServer: {
    command: `npm start`,
    port: Number(PORT),
    reuseExistingServer: true,
    timeout: 120 * 1000, // 2 minutes
  },
  use: {
    baseURL: FRONTEND_APP_URL,
  },
});
