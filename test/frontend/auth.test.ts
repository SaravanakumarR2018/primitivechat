import { test, expect } from '@playwright/test';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config({ path: 'src/frontend/.env' });

const FRONTEND_APP_URL = process.env.FRONTEND_APP_URL;

test('User can sign in and see the dashboard', async ({ page }) => {
  // Go to the home page
  await page.goto(`${FRONTEND_APP_URL}`);

  // Click on the sign-in option
  await page.click('text=Sign In');

  // Fill in the credentials and submit the form
  await page.fill('input[name="email"]', 'test@test.com');
  await page.fill('input[name="password"]', 'acchair123');
  await page.click('button[type="submit"]');

  // Wait for navigation to the dashboard
  await page.waitForNavigation();

  // Check if the user is on the dashboard
  await expect(page).toHaveURL(`${FRONTEND_APP_URL}/dashboard`);

  // Check if the organization is present on the dashboard
  await expect(page.locator('text=simple')).toBeVisible();
});