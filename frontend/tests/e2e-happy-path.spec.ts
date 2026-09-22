import { test, expect, Page, Route } from '@playwright/test';
import path from 'path';

// ─── API Mock Helpers ──────────────────────────────────────────────────────────
const MOCK_TOKEN = 'mock-jwt-token';
const MOCK_BILL_ID = 'e2e-bill-001';
const MOCK_REPORT_ID = 'e2e-report-001';

async function setupMockRoutes(page: Page) {
  // Auth — login
  await page.route('**/api/v1/auth/login', (route: Route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        data: { token: MOCK_TOKEN, expires_in: 3600 },
      }),
    });
  });

  // Bills — upload
  await page.route('**/api/v1/bills/upload', (route: Route) => {
    route.fulfill({
      status: 202,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        data: { bill_id: MOCK_BILL_ID, message: 'Bill accepted for processing.' },
      }),
    });
  });

  // Bills — get (first: PROCESSING, then: COMPLETED)
  let billCallCount = 0;
  await page.route(`**/api/v1/bills/${MOCK_BILL_ID}`, (route: Route) => {
    billCallCount++;
    if (billCallCount === 1) {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: { bill_id: MOCK_BILL_ID, status: 'PROCESSING' },
        }),
      });
    } else {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: {
            bill_id: MOCK_BILL_ID,
            status: 'COMPLETED',
            extracted_data: {
              utility_type: 'ELECTRICITY',
              consumption: 4500,
              unit: 'kWh',
              billing_period_start: '2026-01-01',
              billing_period_end: '2026-01-31',
              cost: 1200.50,
            },
            emissions: { calculated_co2e_kg: 2025.0, scope: 'SCOPE_2' },
          },
        }),
      });
    }
  });

  // Emissions — summary
  await page.route('**/api/v1/emissions/summary**', (route: Route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        data: {
          total_co2e_kg: 2025.0,
          breakdown: { 'SCOPE_1': 0, 'SCOPE_2': 2025.0, 'SCOPE_3': 0 },
        },
      }),
    });
  });

  // Chat
  await page.route('**/api/v1/chat/query', (route: Route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        data: {
          answer: 'Electricity consumption falls under Scope 2 per GHG Protocol.',
          sources: ['GHG Protocol Corporate Standard - Chapter 4'],
          confidence_score: 0.92,
        },
      }),
    });
  });

  // Reports — generate
  await page.route('**/api/v1/reports/generate', (route: Route) => {
    route.fulfill({
      status: 202,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        data: { report_id: MOCK_REPORT_ID },
      }),
    });
  });

  // Reports — get status
  await page.route(`**/api/v1/reports/${MOCK_REPORT_ID}`, (route: Route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        data: {
          report_id: MOCK_REPORT_ID,
          status: 'COMPLETED',
          download_url: 'https://example.com/mock-report.pdf',
        },
      }),
    });
  });
}

// ─── Tests ────────────────────────────────────────────────────────────────────
test.describe('Full Happy Path', () => {
  test.beforeEach(async ({ page }) => {
    await setupMockRoutes(page);
  });

  test('complete flow: login → upload → poll → dashboard → chat → report → download', async ({ page }) => {
    // ── Step 1: Login ──────────────────────────────────────────────────────────
    await page.goto('/login');
    // Login page has a card title, not a heading — check for the sign-in button
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();

    await page.getByLabel(/email/i).fill('user@example.com');
    await page.getByLabel(/password/i).fill('securepassword123');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should redirect away from /login
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
    await expect(page).not.toHaveURL(/\/login/);

    // ── Step 2: Upload ─────────────────────────────────────────────────────────
    await page.goto('/upload');
    await expect(page.locator('text=Upload Utility Bill').first()).toBeVisible();

    const fixturePath = path.join(__dirname, 'fixtures', 'sample-bill.pdf');
    await page.locator('input[type="file"]').setInputFiles(fixturePath);
    await expect(page.getByText('sample-bill.pdf')).toBeVisible();

    await page.getByRole('button', { name: /upload and process/i }).click();

    // Redirect to bill details
    await page.waitForURL(`**/bills/${MOCK_BILL_ID}`, { timeout: 10000 });

    // ── Step 3: Poll details until COMPLETED ───────────────────────────────────
    await expect(page.getByText('Status: PROCESSING')).toBeVisible({ timeout: 5000 });
    // TanStack Query will refetch — mock returns COMPLETED on second call
    await expect(page.getByText('Status: COMPLETED')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('input[value="ELECTRICITY"], select option[selected]').or(page.getByText('ELECTRICITY'))).toBeVisible();
    await expect(page.getByText(/2025/).first()).toBeVisible();

    // ── Step 4: Dashboard ──────────────────────────────────────────────────────
    await page.goto('/dashboard');
    // Should NOT show empty state
    await expect(page.getByText(/no data yet/i)).not.toBeVisible();
    // Should show CO2e value from mock
    await expect(page.getByText(/2,025/).first()).toBeVisible({ timeout: 10000 });

    // ── Step 5: Chat ──────────────────────────────────────────────────────────
    await page.goto('/chat');
    await expect(page.getByText(/compliance chat/i).first()).toBeVisible();

    await page.getByPlaceholder(/ask a question/i).fill('Is electricity consumption Scope 2?');
    await page.getByRole('button', { name: /send/i }).click();

    await expect(page.getByText('Is electricity consumption Scope 2?')).toBeVisible();
    await expect(
      page.getByText(/Electricity consumption falls under Scope 2/i)
    ).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/GHG Protocol/i).first()).toBeVisible();

    // ── Step 6: Generate report ────────────────────────────────────────────────
    await page.goto('/reports');
    await expect(page.locator('h1').filter({ hasText: /generate report/i })).toBeVisible();

    await page.getByLabel(/period start/i).fill('2026-01-01');
    await page.getByLabel(/period end/i).fill('2026-06-30');
    await page.getByRole('button', { name: /generate report/i }).click();

    await expect(page.getByText(/report ready/i)).toBeVisible({ timeout: 15000 });

    const downloadLink = page.getByRole('button', { name: /download report/i }).locator('..');
    await expect(downloadLink).toHaveAttribute('href', 'https://example.com/mock-report.pdf');
  });

  test('login: shows validation errors for bad input', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: /sign in/i }).click();

    // react-hook-form renders errors as <p class="text-sm text-ink-secondary">
    // The message for empty email is "Invalid email address"
    await expect(page.getByText('Invalid email address')).toBeVisible({ timeout: 5000 });
  });

  test('upload: rejects files larger than 15MB', async ({ page }) => {
    await page.goto('/upload');

    // Simulate a large file via JS
    await page.evaluate(() => {
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      const largeFile = new File(
        [new Uint8Array(16 * 1024 * 1024).fill(0)],
        'huge-file.pdf',
        { type: 'application/pdf' }
      );
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(largeFile);
      input.files = dataTransfer.files;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });

    // Filter out Next.js route announcer
    await expect(
      page.getByRole('alert').filter({ hasText: /file too large/i })
    ).toBeVisible({ timeout: 5000 });
  });

  test('reports: validates date range', async ({ page }) => {
    await page.goto('/reports');

    await page.getByLabel(/period start/i).fill('2026-06-01');
    await page.getByLabel(/period end/i).fill('2026-01-01');
    await page.getByRole('button', { name: /generate report/i }).click();

    // Filter out Next.js route announcer
    await expect(
      page.getByRole('alert').filter({ hasText: /strictly before/i })
    ).toBeVisible({ timeout: 5000 });
  });
});
