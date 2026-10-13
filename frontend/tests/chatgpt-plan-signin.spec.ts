import { test, expect } from "@playwright/test";

const localSignInURL = process.env.LANES_CHATGPT_SIGNIN_URL;
test.skip(!localSignInURL, "Opt-in local sign-in helper checks; set LANES_CHATGPT_SIGNIN_URL.");

// The local pilot is opened in Chrome. Retain each project's desktop/mobile device settings.
test.use({ browserName: "chromium", ...(localSignInURL ? { baseURL: localSignInURL } : {}) });

test("local ChatGPT connection page explains permission and has no horizontal overflow", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "LANES ChatGPT connection" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Continue with ChatGPT" })).toBeVisible();
  await expect(page.getByText(/It does not run news audits or publish alerts/)).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  const response = await page.request.get("/status");
  expect(response.ok()).toBeTruthy();
  const status = await response.json();
  expect(status.inference_verified).toBe(false);
  expect(status.news_worker_enabled).toBe(false);
  await page.screenshot({ path: `../data/mcp-research/chatgpt-signin-${test.info().project.name}.png` });
});

test("Chrome sends its real local origin when Continue is clicked", async ({ page }) => {
  const origin = new URL(localSignInURL as string).origin;
  await page.goto("/");
  let formOrigin: string | undefined;
  // Capture the real browser POST without starting an OAuth attempt on the user's helper.
  await page.route("**/connect", async route => {
    formOrigin = route.request().headers().origin;
    await route.fulfill({ status: 200, contentType: "text/html", body: "Button request checked" });
  });
  await page.getByRole("button", { name: "Continue with ChatGPT" }).click();
  await expect(page.getByText("Button request checked")).toBeVisible();
  expect(formOrigin).toBe(origin);
});
