import { test, expect } from '@playwright/test';

test.describe('Tenant Setup Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tenant-setup');
  });

  test('should display tenant setup form', async ({ page }) => {
    // Check that tenant setup page loads correctly
    await expect(page).toHaveTitle(/Tenant Setup - Requirements Generator/);

    // Check for key UI elements
    await expect(page.locator('h1, h2').first()).toContainText(/Setup.*Organization/i);

    // Check for tenant setup fields
    await expect(page.locator('input[name="name"], input[name="organization_name"]')).toBeVisible();
    await expect(page.locator('input[name="subdomain"]')).toBeVisible();

    // Check for industry selection
    const industrySelect = page.locator('select[name="industry"]');
    if (await industrySelect.count() > 0) {
      await expect(industrySelect).toBeVisible();
    }

    // Check for submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit without filling required fields
    await page.click('button[type="submit"]');

    // Check for required field validation
    const nameInput = page.locator('input[name="name"], input[name="organization_name"]').first();
    const subdomainInput = page.locator('input[name="subdomain"]');

    await expect(nameInput).toHaveAttribute('required');
    await expect(subdomainInput).toHaveAttribute('required');
  });

  test('should validate subdomain format', async ({ page }) => {
    const subdomainInput = page.locator('input[name="subdomain"]');

    // Test invalid subdomain characters
    await subdomainInput.fill('invalid subdomain!');

    // The input should either prevent invalid characters or show validation
    const value = await subdomainInput.inputValue();
    // Subdomain should only contain alphanumeric and hyphens
    expect(value).toMatch(/^[a-zA-Z0-9-]*$/);
  });

  test('should show subdomain availability check', async ({ page }) => {
    const subdomainInput = page.locator('input[name="subdomain"]');

    // Fill subdomain
    await subdomainInput.fill('test-company');

    // Should trigger availability check (if implemented)
    await page.waitForTimeout(1000);

    // Look for any availability indicators
    const availabilityMessage = page.locator('[data-testid="subdomain-availability"], .subdomain-check, .availability');
    if (await availabilityMessage.count() > 0) {
      await expect(availabilityMessage).toBeVisible();
    }
  });

  test('should handle industry selection', async ({ page }) => {
    const industrySelect = page.locator('select[name="industry"]');

    if (await industrySelect.count() > 0) {
      // Select an industry
      await industrySelect.selectOption('banking');

      // Verify selection
      await expect(industrySelect).toHaveValue('banking');
    }
  });

  test('should submit tenant setup form', async ({ page }) => {
    // Fill out the form
    const nameInput = page.locator('input[name="name"], input[name="organization_name"]').first();
    await nameInput.fill('Test Organization');

    await page.fill('input[name="subdomain"]', 'test-org-123');

    // Select industry if available
    const industrySelect = page.locator('select[name="industry"]');
    if (await industrySelect.count() > 0) {
      await industrySelect.selectOption('banking');
    }

    // Submit form
    await page.click('button[type="submit"]');

    // Should show loading state
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeDisabled();

    // Wait for response
    await page.waitForTimeout(3000);

    // Note: Actual behavior depends on implementation
    // This test validates the UI interaction
  });
});

test.describe('Tenant Selection Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tenant-select');
  });

  test('should display tenant selection page', async ({ page }) => {
    // Check that tenant select page loads
    await expect(page).toHaveTitle(/Select Organization - Requirements Generator/);

    // Should show options to join or create tenant
    const createButton = page.locator('button, a').filter({ hasText: /Create.*Organization/i });
    const joinSection = page.locator('[data-testid="join-tenant"], .join-tenant');

    // At least one of these should be visible
    const hasCreateButton = await createButton.count() > 0;
    const hasJoinSection = await joinSection.count() > 0;

    expect(hasCreateButton || hasJoinSection).toBeTruthy();
  });

  test('should navigate to tenant setup', async ({ page }) => {
    // Look for create organization button/link
    const createButton = page.locator('button, a').filter({ hasText: /Create.*Organization/i }).first();

    if (await createButton.count() > 0) {
      await createButton.click();

      // Should navigate to tenant setup
      await expect(page).toHaveURL(/.*tenant-setup/);
    }
  });

  test('should show invitation code input', async ({ page }) => {
    // Look for invitation/join section
    const invitationInput = page.locator('input[name="invitation_code"], input[name="token"]');

    if (await invitationInput.count() > 0) {
      await expect(invitationInput).toBeVisible();

      // Test filling invitation code
      await invitationInput.fill('test-invitation-123');

      const joinButton = page.locator('button').filter({ hasText: /Join/i });
      if (await joinButton.count() > 0) {
        await expect(joinButton).toBeVisible();
      }
    }
  });
});

test.describe('Dashboard Access', () => {
  test('should display dashboard for authenticated users', async ({ page }) => {
    await page.goto('/dashboard');

    // Depending on auth state, should either show dashboard or redirect to login
    await page.waitForTimeout(2000);

    const currentUrl = page.url();

    if (currentUrl.includes('/login')) {
      // Redirected to login - expected for unauthenticated users
      await expect(page).toHaveTitle(/Login - Requirements Generator/);
    } else if (currentUrl.includes('/dashboard')) {
      // On dashboard - check for dashboard elements
      await expect(page).toHaveTitle(/Dashboard - Requirements Generator/);

      // Look for common dashboard elements
      const dashboardElements = [
        page.locator('h1, h2').filter({ hasText: /Dashboard/i }),
        page.locator('[data-testid="dashboard"]'),
        page.locator('.dashboard-content'),
        page.locator('nav, .navigation')
      ];

      // At least one dashboard element should be visible
      let foundDashboardElement = false;
      for (const element of dashboardElements) {
        if (await element.count() > 0) {
          foundDashboardElement = true;
          break;
        }
      }

      expect(foundDashboardElement).toBeTruthy();
    }
  });

  test('should show navigation menu', async ({ page }) => {
    await page.goto('/dashboard');

    // Wait for page load
    await page.waitForTimeout(2000);

    // If on dashboard, check for navigation
    if (page.url().includes('/dashboard')) {
      const navigation = page.locator('nav, .navigation, [role="navigation"]');

      if (await navigation.count() > 0) {
        await expect(navigation).toBeVisible();

        // Look for common nav items
        const navItems = [
          page.locator('a, button').filter({ hasText: /Dashboard/i }),
          page.locator('a, button').filter({ hasText: /Projects/i }),
          page.locator('a, button').filter({ hasText: /Users/i }),
          page.locator('a, button').filter({ hasText: /Settings/i }),
          page.locator('a, button').filter({ hasText: /Logout/i })
        ];

        // At least some nav items should be present
        let visibleNavItems = 0;
        for (const item of navItems) {
          if (await item.count() > 0) {
            visibleNavItems++;
          }
        }

        expect(visibleNavItems).toBeGreaterThan(0);
      }
    }
  });
});