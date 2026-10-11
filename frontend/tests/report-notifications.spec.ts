import { expect as baseExpect, test, type Page } from "@playwright/test";
import type { Notification } from "../src/features/notifications/notificationsApi";

const expect = baseExpect.configure({ timeout: 30_000 });
test.setTimeout(90_000);
test.use({ browserName: 'chromium' });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: {
  executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
} });

const hydrationErrors = new WeakMap<Page, string[]>();
test.beforeEach(({ page }) => {
  const errors: string[] = [];
  hydrationErrors.set(page, errors);
  const recordHydrationError = (message: string) => {
    if (/hydration|server rendered HTML/i.test(message)) errors.push(message);
  };
  page.on('pageerror', error => recordHydrationError(error.message));
  page.on('console', message => {
    if (message.type() === 'error') recordHydrationError(message.text());
  });
});
test.afterEach(({ page }) => {
  expect(hydrationErrors.get(page) ?? [], 'Server/client renders must hydrate without errors').toEqual([]);
});

const report = {
  id: 42, source: "direct_user", raw_text: "My private flood report at the bridge.",
  status: "approved", severity: "medium", depth: "knee", created_at: "2026-10-11T01:00:00Z",
  geometry: null, barangay: "Maybunga", city: "Pasig", is_bidirectional: false,
  survey: { hidden_hazards: "yes", passable_vehicles: "heavy" }, reporter_name: "Test Citizen",
};
const actions = ["under_review", "approved", "rejected"];
const titles = ["Flood Report Under Review", "Flood Report Approved", "Flood Report Rejected"];
const messages = ["Your report is awaiting review.", "Your report has been reviewed and approved.",
  "Your flood report was reviewed and was not added to the live map because it had insufficient supporting evidence."];

async function setup(page: Page) {
  const notices: Notification[] = actions.map((action, index) => ({ id: index + 1, user_id: 7, type: "SYSTEM",
    message: messages[index], payload: { action: `flood_report_${action}`, title: titles[index], report_id: 42 },
    is_read: false, created_at: "2026-10-11T01:00:00Z" }));
  const state = { unavailable: false, wrongReport: false, readFailure: false, listFailure: false };
  const readRequests: number[] = [];
  const reportRequests: string[] = [];
  await page.addInitScript(() => localStorage.setItem("lanes_token", "test-only-token"));
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    let body: unknown = [];
    if (path.endsWith('/news/local-updates')) return route.fulfill({ json: { items: [], as_of: report.created_at } });
    if (path.endsWith('/feed/leaderboard')) return route.fulfill({ json: { reporters: [] } });
    if (path.endsWith("/auth/test-token")) body = { id: 7, username: "citizen", is_active: true, role: { name: "Commuter" } };
    else if (path.endsWith("/notifications")) {
      if (state.listFailure) return route.fulfill({ status: 500, json: { detail: "Notifications unavailable" } });
      body = { notifications: notices, total: notices.length,
        unread_count: notices.filter(n => !n.is_read).length, has_more: false };
    } else if (/\/notifications\/\d+\/read$/.test(path)) {
      const id = Number(path.split("/").at(-2));
      readRequests.push(id);
      if (state.readFailure) return route.fulfill({ status: 500, json: { detail: "Unable to mark notification as read" } });
      const notice = notices.find(n => n.id === id)!;
      notice.is_read = true;
      body = notice;
    } else if (path.endsWith("/notifications/read-all")) {
      if (state.readFailure) return route.fulfill({ status: 500, json: { detail: "Unable to mark notifications as read" } });
      notices.forEach(n => { n.is_read = true; }); body = { message: "All notifications marked as read" };
    } else if (path.endsWith("/reports/me/42")) {
      reportRequests.push(path);
      if (state.unavailable) return route.fulfill({ status: 404, json: { detail: "Flood report unavailable" } });
      body = { ...report, id: state.wrongReport ? 99 : 42 };
    } else if (path.endsWith('/posts/31')) body = { id: 31, user_id: 7, content: 'My reported community post',
      author_name: 'Test Citizen', created_at: report.created_at, updated_at: report.created_at,
      upvotes: 0, downvotes: 0, comment_count: 0 };
    else if (path.endsWith('/feed/hotspots')) body = { hotspots: [], window_hours: 24, as_of: report.created_at };
    else if (path.endsWith('/feed') || /\/posts\/?$/.test(path)) body = { posts: [], total: 0, has_more: false };
    return route.fulfill({ json: body });
  });
  await page.goto("/feed");
  const bell = page.getByRole("button", { name: "Notifications", exact: true });
  await expect(bell).toContainText("3");
  await bell.click();
  return { notices, state, readRequests, reportRequests, bell };
}

test("status notices display distinct titles, reasons and timestamps within the viewport", async ({ page }, testInfo) => {
  await setup(page);
  for (const title of titles) await expect(page.getByRole("button", { name: new RegExp(title) })).toBeVisible();
  await expect(page.getByText(/insufficient supporting evidence/)).toBeVisible();
  await expect(page.locator("#notification-bell").getByText(/Oct 11/)).toHaveCount(3);
  const panel = page.getByRole("heading", { name: "Notifications", exact: true }).locator("../..");
  const bounds = await panel.boundingBox();
  expect(bounds).not.toBeNull();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await page.screenshot({ path: testInfo.outputPath("notification-bell.png"), animations: 'disabled' });
});

for (const title of titles) {
  test(`${title} opens the correct owner report and updates unread count`, async ({ page }, testInfo) => {
    const { readRequests, reportRequests, bell } = await setup(page);
    await page.getByRole("button", { name: new RegExp(title) }).click();
    const dialog = page.getByRole("dialog", { name: "Flood Report Details" });
    await expect(dialog).toBeVisible();
    await expect(dialog).toHaveCSS('opacity', '1');
    await expect(dialog.locator(':scope > div').first()).toHaveCSS('opacity', '1');
    await expect.poll(() => dialog.getByRole('heading', { name: 'Flood Report Details', exact: true }).evaluate(element => {
      const bounds = element.getBoundingClientRect();
      return Boolean(document.elementFromPoint(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2)?.closest('[role="dialog"]'));
    })).toBe(true);
    await expect(dialog.getByText(report.raw_text, { exact: false })).toBeVisible();
    await expect(dialog.getByText("#42", { exact: true })).toBeVisible();
    await expect(bell).toContainText("2");
    expect(readRequests).toEqual([titles.indexOf(title) + 1]);
    expect(reportRequests).toEqual(["/api/v1/reports/me/42"]);
    await page.screenshot({ path: testInfo.outputPath("notification-report-details.png"), animations: 'disabled' });
    await page.getByRole("button", { name: "Close flood report details" }).click();
    await bell.click();
    await page.getByRole("button", { name: new RegExp(title) }).click();
    await expect(dialog).toBeVisible();
    expect(readRequests).toHaveLength(1);
  });
}

test("missing and mismatched reports show an error without opening another report", async ({ page }) => {
  const { state, bell } = await setup(page);
  state.unavailable = true;
  await page.getByRole("button", { name: /Flood Report Approved/ }).click();
  await expect(page.locator('#notification-bell').getByRole("alert")).toHaveText("Flood report unavailable");
  await expect(page.getByRole("dialog", { name: "Flood Report Details" })).toHaveCount(0);
  await expect(bell).toContainText("2");
  state.unavailable = false; state.wrongReport = true;
  await page.getByRole("button", { name: /Flood Report Approved/ }).click();
  await expect(page.locator('#notification-bell').getByRole("alert")).toHaveText("The requested flood report is unavailable.");
  await expect(page.getByRole("dialog", { name: "Flood Report Details" })).toHaveCount(0);
});

test("read failures remain visible and do not open report details", async ({ page }) => {
  const { state, reportRequests, bell } = await setup(page);
  state.readFailure = true;
  await page.getByRole("button", { name: /Flood Report Approved/ }).click();
  await expect(page.locator('#notification-bell').getByRole("alert")).toHaveText("Unable to mark notification as read");
  expect(reportRequests).toHaveLength(0);
  await expect(bell).toContainText("3");
  await page.getByRole("button", { name: "Mark all as read" }).click();
  await expect(page.locator('#notification-bell').getByRole("alert")).toHaveText("Could not mark notifications as read. Please try again.");
  state.readFailure = false;
  await page.getByRole("button", { name: "Mark all as read" }).click();
  await expect(bell).not.toContainText("3");
  await expect(page.getByRole("button", { name: "Mark all as read" })).toHaveCount(0);
});

test("notification fetch failures offer retry", async ({ page }) => {
  const { state, bell } = await setup(page);
  state.listFailure = true;
  await page.reload();
  await page.getByRole("button", { name: "Notifications", exact: true }).click();
  await expect(page.locator('#notification-bell').getByRole("alert")).toContainText("Could not load notifications");
  state.listFailure = false;
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(bell).toContainText("3");
  await expect(page.locator('#notification-bell').getByRole("alert")).toHaveCount(0);
});

test("existing reported-post warnings remain distinguishable and open the associated post", async ({ page }) => {
  const { notices, readRequests } = await setup(page);
  notices[2].message = 'A moderator warned you about a Community Feed post. Reason: Misinformation / False Hazard.';
  notices[2].payload = { post_id: 31, action: 'warn', reasons: ['Misinformation / False Hazard'] };
  await page.reload();
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await page.getByRole('button', { name: /A moderator warned you/ }).click();
  await expect(page).toHaveURL(/\/feed\/31$/, { timeout: 60_000 });
  await expect(page.getByText('My reported community post', { exact: true }).first()).toBeVisible();
  expect(readRequests).toEqual([3]);
});

test('legacy rejection notices retain the reason and receive a clear title', async ({ page }) => {
  const { notices } = await setup(page);
  delete notices[2].payload!.title;
  await page.reload();
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.getByRole('button', { name: /Flood Report Rejected.*insufficient supporting evidence/ })).toBeVisible();
});
