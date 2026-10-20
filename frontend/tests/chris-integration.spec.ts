import { expect, test } from '@playwright/test';
import { expectNoOverflow, installChrisFixtures } from './helpers/chrisIntegration';

test.setTimeout(120_000);
test.use({ browserName: 'chromium', actionTimeout: 30_000, launchOptions: { args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] } });

test('legal notices scroll, close with Escape and restore trigger focus', async ({ page }, info) => {
  const state = await installChrisFixtures(page, null);
  await page.goto('/register');
  for (const notice of ['Privacy Policy', 'Terms of Service']) {
    const trigger = page.getByRole('button', { name: notice, exact: true }).first();
    await trigger.click();
    const dialog = page.getByRole('dialog', { name: notice, exact: true });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('button', { name: `Close ${notice}` })).toBeFocused();
    await dialog.getByRole('heading', { name: notice === 'Privacy Policy' ? '8. Updates to this notice' : '7. Changes and contact' }).scrollIntoViewIfNeeded();
    await expectNoOverflow(page);
    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden();
    await expect(trigger).toBeFocused();
  }
  await page.screenshot({ animations: 'disabled', timeout: 30_000, path: info.outputPath('legal-registration.png') });
  expect(state.errors).toEqual([]);
});

test('Flood Events dialog escapes page stacking and preserves historical evidence', async ({ page }, info) => {
  const state = await installChrisFixtures(page, 'Admin');
  await page.goto('/admin/flood-history');
  await page.getByRole('button', { name: 'Flood Events', exact: true }).click();
  await page.getByRole('button', { name: 'View event', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Flood Event Details' });
  await expect(dialog).toBeVisible();
  expect(await dialog.evaluate(element => element.parentElement === document.body)).toBe(true);
  await expect(dialog.getByRole('heading', { name: 'Flood Event Details' })).toBeVisible();
  await page.screenshot({ animations: 'disabled', timeout: 30_000, path: info.outputPath('flood-event-dialog.png') });
  await page.getByRole('button', { name: 'Close flood event details' }).click();
  await expect(dialog).toBeHidden();
  await expectNoOverflow(page);
  expect(state.errors).toEqual([]);
});

test('saved place pins toggle, selection focuses map and logout removes pins', async ({ page }, info) => {
  const state = await installChrisFixtures(page);
  await page.goto('/map?panel=saveplace&tab=list');
  await expect(page.getByRole('button', { name: 'Show saved place pins' })).toBeVisible();
  const markers = page.locator('.maplibregl-marker').filter({ hasText: /Fixture Home|Fixture Work/ });
  await expect(markers).toHaveCount(0);
  await page.getByRole('button', { name: 'Show saved place pins' }).click();
  await expect(markers).toHaveCount(2);
  await page.getByRole('button', { name: 'Hide saved place pins' }).click();
  await expect(markers).toHaveCount(0);
  await page.getByRole('heading', { name: 'Fixture Home', exact: true })
    .locator('xpath=ancestor::div[contains(@class, "cursor-pointer")][1]').click();
  await expect(markers).toHaveCount(1);
  await expect.poll(() => page.evaluate(() => JSON.parse(sessionStorage.getItem('lanes_map_viewport') || '{}').zoom)).toBeGreaterThanOrEqual(15.9);
  await page.screenshot({ animations: 'disabled', timeout: 30_000, path: info.outputPath('saved-place-selection.png') });
  if (info.project.name === 'mobile-chromium') {
    await page.locator('nav.fixed.bottom-0').getByRole('link', { name: 'Profile', exact: true }).click();
    await page.getByRole('button', { name: 'Settings', exact: true }).last().click();
    await page.getByRole('button', { name: 'Log Out', exact: true }).last().click();
    await page.getByRole('button', { name: 'Yes, Log Out', exact: true }).click();
  } else await page.getByRole('button', { name: /Log Out/ }).first().click();
  await expect(markers).toHaveCount(0);
  expect(await page.evaluate(() => localStorage.getItem('lanes_token'))).toBeNull();
  expect(state.errors).toEqual([]);
});

test('admin View on map focuses selected zone and opens mobile map', async ({ page }, info) => {
  const state = await installChrisFixtures(page, 'Admin');
  await page.goto('/admin/map');
  await page.getByRole('button', { name: /Active Zones/ }).first().click();
  await page.getByRole('button', { name: 'View on map', exact: true }).click();
  if (info.project.name === 'mobile-chromium') await expect(page.getByRole('region', { name: 'Active Zones' })).toBeHidden();
  await expect(page.locator('.maplibregl-canvas').first()).toBeVisible();
  await expect.poll(() => page.locator('[title^="Zoom:"]').first().getAttribute('title')).toMatch(/Zoom: 1[6-9]/);
  await page.screenshot({ animations: 'disabled', timeout: 30_000, path: info.outputPath('admin-zone-focus.png') });
  await expectNoOverflow(page);
  expect(state.errors).toEqual([]);
});

test('profile final controls remain above mobile navigation', async ({ page }, info) => {
  const state = await installChrisFixtures(page);
  await page.goto('/profile');
  await page.getByRole('button', { name: 'Settings', exact: true }).last().click();
  const lastAction = page.getByRole('button', { name: info.project.name === 'mobile-chromium' ? 'Log Out' : 'Delete Account', exact: true }).last();
  await lastAction.scrollIntoViewIfNeeded();
  await expect(lastAction).toBeVisible();
  const bounds = await lastAction.boundingBox();
  const bottom = info.project.name === 'mobile-chromium'
    ? (await page.locator('nav.fixed.bottom-0').boundingBox())!.y : page.viewportSize()!.height;
  expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(bottom);
  await expectNoOverflow(page);
  await page.screenshot({ animations: 'disabled', timeout: 30_000, path: info.outputPath('profile-bottom-spacing.png') });
  expect(state.errors).toEqual([]);
});

test('route instructions focus map and mobile selection stays highlighted', async ({ page }, info) => {
  const state = await installChrisFixtures(page);
  await page.goto('/map');
  if (info.project.name === 'mobile-chromium') await page.getByText('Tap to plan route', { exact: true }).click();
  await page.getByPlaceholder('Your location', { exact: true }).fill('Fixture Origin');
  await expect(page.getByRole('button', { name: /^Fixture Origin/ }).last()).toBeVisible();
  await page.getByPlaceholder('Your location', { exact: true }).press('ArrowDown');
  await page.getByPlaceholder('Your location', { exact: true }).press('Enter');
  await page.getByPlaceholder('Choose destination', { exact: true }).fill('Fixture Destination');
  await expect(page.getByRole('button', { name: /^Fixture Destination/ }).last()).toBeVisible();
  await page.getByPlaceholder('Choose destination', { exact: true }).press('ArrowDown');
  await page.getByPlaceholder('Choose destination', { exact: true }).press('Enter');
  const step = page.getByRole('button', { name: /Continue along Fixture Road/ });
  if (info.project.name === 'mobile-chromium') await page.locator('div.cursor-grab').last().click();
  await step.click();
  await expect.poll(() => page.evaluate(() => JSON.parse(sessionStorage.getItem('lanes_map_viewport') || '{}').zoom)).toBeGreaterThanOrEqual(16);
  if (info.project.name === 'mobile-chromium') {
    await page.mouse.move(10, 100);
    await expect.poll(async () => {
      const png = await page.locator('.maplibregl-canvas').first().screenshot({ animations: 'disabled' });
      return page.evaluate(async base64 => {
        const image = new Image(); image.src = `data:image/png;base64,${base64}`; await image.decode();
        const canvas = document.createElement('canvas'); canvas.width = image.width; canvas.height = image.height;
        const context = canvas.getContext('2d')!; context.drawImage(image, 0, 0);
        const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
        let highlighted = 0;
        for (let index = 0; index < pixels.length; index += 4) {
          if (pixels[index] < 70 && pixels[index + 1] > 145 && pixels[index + 1] < 200 && pixels[index + 2] > 210) highlighted++;
        }
        return highlighted;
      }, png.toString('base64'));
    }).toBeGreaterThan(10);
  }
  await page.screenshot({ animations: 'disabled', timeout: 30_000, path: info.outputPath('route-step-focus.png') });
  expect(state.requests).toContain('POST /api/v1/reports/route');
  expect(state.errors).toEqual([]);
});

test('mobile feed drawer keeps final navigation reachable above bottom bar', async ({ page }, info) => {
  test.skip(info.project.name !== 'mobile-chromium', 'The drawer is replaced by the desktop sidebar.');
  const state = await installChrisFixtures(page);
  await page.goto('/feed');
  await page.getByRole('button', { name: 'Open navigation menu' }).click();
  const scroller = page.locator('[data-lenis-prevent]').filter({ has: page.getByRole('heading', { name: 'Navigation', exact: true }) });
  await expect(scroller).toBeVisible();
  await scroller.evaluate(element => { element.scrollTop = element.scrollHeight; });
  // Check the final action, rather than the drawer border next to the nav border.
  const bounds = await scroller.getByRole('button', { name: 'Add a Place', exact: true }).boundingBox();
  const nav = page.locator('nav').filter({ has: page.getByRole('link', { name: 'Profile', exact: true }) }).last();
  const navBounds = await nav.boundingBox();
  expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(navBounds?.y ?? page.viewportSize()!.height);
  await page.screenshot({ animations: 'disabled', timeout: 30_000, path: info.outputPath('feed-drawer-bottom.png') });
  expect(state.errors).toEqual([]);
});

test('mobile flood end selection returns to report panel', async ({ page }, info) => {
  test.skip(info.project.name !== 'mobile-chromium', 'Desktop keeps the report panel beside the map.');
  const state = await installChrisFixtures(page);
  await page.goto('/map');
  await page.getByRole('button', { name: 'Report Flood Hazard', exact: true }).click();
  await page.getByRole('button', { name: 'Flood Report', exact: true }).click();
  const start = page.getByPlaceholder('e.g. Ortigas Ave, Pasig (Start)', { exact: true });
  await start.click();
  await page.getByRole('button', { name: 'Choose on Map', exact: true }).first().click();
  const canvas = page.locator('.maplibregl-canvas').first();
  await expect(canvas).toBeVisible();
  const bounds = await canvas.boundingBox();
  await page.mouse.move(bounds!.x + bounds!.width / 2, bounds!.y + bounds!.height / 2);
  await page.mouse.down();
  await page.mouse.move(bounds!.x + bounds!.width / 2 + 50, bounds!.y + bounds!.height / 2, { steps: 8 });
  await page.mouse.up();
  await page.getByRole('button', { name: 'Set Flood Start', exact: true }).click();
  await page.getByRole('button', { name: 'Set Flood End', exact: true }).click();
  await expect(start).toBeVisible();
  await expect(start).not.toHaveValue('');
  await expect(page.getByPlaceholder('e.g. C. Raymundo Ave (End)', { exact: true })).not.toHaveValue('');
  await page.screenshot({ animations: 'disabled', timeout: 30_000, path: info.outputPath('flood-picker-return.png') });
  expect(state.requests.some(request => request.includes('/reports/submit'))).toBe(false);
  expect(state.errors).toEqual([]);
});
