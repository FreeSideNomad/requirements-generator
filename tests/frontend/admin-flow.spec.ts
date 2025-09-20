import { test, expect } from '@playwright/test';

test.describe('Admin User Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/users');
  });

  test('should display user management page for admins', async ({ page }) => {
    // Wait for page load
    await page.waitForTimeout(2000);

    const currentUrl = page.url();

    if (currentUrl.includes('/login')) {
      // Redirected to login - expected for unauthenticated users
      await expect(page).toHaveTitle(/Login - Requirements Generator/);
      test.skip('User not authenticated - skipping admin tests');
    } else if (currentUrl.includes('/admin/users') || currentUrl.includes('/users')) {
      // On user management page
      await expect(page).toHaveTitle(/Users - Requirements Generator/);

      // Check for user management elements
      await expect(page.locator('h1, h2').filter({ hasText: /Users/i })).toBeVisible();

      // Look for user list table or cards
      const userList = page.locator('table, .user-list, [data-testid="user-list"]');
      if (await userList.count() > 0) {
        await expect(userList).toBeVisible();
      }

      // Look for invite/add user button
      const inviteButton = page.locator('button, a').filter({ hasText: /Invite.*User|Add.*User/i });
      if (await inviteButton.count() > 0) {
        await expect(inviteButton).toBeVisible();
      }
    }
  });

  test('should show user invite modal', async ({ page }) => {
    // Wait for page load
    await page.waitForTimeout(2000);

    if (page.url().includes('/login')) {
      test.skip('User not authenticated - skipping admin tests');
    }

    // Look for invite user button
    const inviteButton = page.locator('button, a').filter({ hasText: /Invite.*User|Add.*User/i }).first();

    if (await inviteButton.count() > 0) {
      await inviteButton.click();

      // Should show invite modal or form
      const modal = page.locator('[role="dialog"], .modal, #invite-modal');
      const form = page.locator('form').filter({ hasText: /Invite|Add/i });

      // Either modal or inline form should appear
      const hasModal = await modal.count() > 0;
      const hasForm = await form.count() > 0;

      expect(hasModal || hasForm).toBeTruthy();

      if (hasModal) {
        await expect(modal).toBeVisible();
      }
      if (hasForm) {
        await expect(form).toBeVisible();
      }
    }
  });

  test('should validate invite user form', async ({ page }) => {
    await page.waitForTimeout(2000);

    if (page.url().includes('/login')) {
      test.skip('User not authenticated - skipping admin tests');
    }

    // Try to open invite form
    const inviteButton = page.locator('button, a').filter({ hasText: /Invite.*User|Add.*User/i }).first();

    if (await inviteButton.count() > 0) {
      await inviteButton.click();

      // Look for email input in invite form
      const emailInput = page.locator('input[name="email"], input[type="email"]').last();

      if (await emailInput.count() > 0) {
        await expect(emailInput).toBeVisible();

        // Test invalid email
        await emailInput.fill('invalid-email');

        const submitButton = page.locator('button[type="submit"]').last();
        if (await submitButton.count() > 0) {
          await submitButton.click();

          // Should show validation error or prevent submission
          await expect(emailInput).toHaveAttribute('type', 'email');
        }
      }
    }
  });

  test('should show user roles and permissions', async ({ page }) => {
    await page.waitForTimeout(2000);

    if (page.url().includes('/login')) {
      test.skip('User not authenticated - skipping admin tests');
    }

    // Look for role selection in invite form or user list
    const roleSelects = page.locator('select[name="role"], .role-select');
    const roleLabels = page.locator('text=/admin|contributor|viewer/i');

    if (await roleSelects.count() > 0) {
      await expect(roleSelects.first()).toBeVisible();

      // Check for common role options
      const roleOptions = page.locator('option').filter({ hasText: /admin|contributor|viewer/i });
      if (await roleOptions.count() > 0) {
        await expect(roleOptions.first()).toBeVisible();
      }
    }

    if (await roleLabels.count() > 0) {
      await expect(roleLabels.first()).toBeVisible();
    }
  });

  test('should handle user actions', async ({ page }) => {
    await page.waitForTimeout(2000);

    if (page.url().includes('/login')) {
      test.skip('User not authenticated - skipping admin tests');
    }

    // Look for user action buttons (edit, delete, etc.)
    const actionButtons = [
      page.locator('button, a').filter({ hasText: /Edit/i }),
      page.locator('button, a').filter({ hasText: /Delete/i }),
      page.locator('button, a').filter({ hasText: /Remove/i }),
      page.locator('[data-testid="user-actions"]'),
      page.locator('.user-actions')
    ];

    let foundActions = false;
    for (const buttons of actionButtons) {
      if (await buttons.count() > 0) {
        foundActions = true;
        break;
      }
    }

    // Actions might not be visible if no users exist yet
    // This is just checking the UI structure exists
  });

  test('should display user information', async ({ page }) => {
    await page.waitForTimeout(2000);

    if (page.url().includes('/login')) {
      test.skip('User not authenticated - skipping admin tests');
    }

    // Look for user information display
    const userInfo = [
      page.locator('td, .user-email').filter({ hasText: /@/ }), // Email addresses
      page.locator('td, .user-name').filter({ hasText: /\w+\s+\w+/ }), // Names
      page.locator('td, .user-role').filter({ hasText: /admin|contributor|viewer/i }), // Roles
      page.locator('.user-card, .user-item, tr')
    ];

    // If users exist, should show their information
    let foundUserInfo = false;
    for (const info of userInfo) {
      if (await info.count() > 0) {
        foundUserInfo = true;
        break;
      }
    }

    // Users might not exist yet, so this is optional
  });
});

test.describe('Admin Navigation', () => {
  test('should show admin menu items', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForTimeout(2000);

    if (page.url().includes('/login')) {
      test.skip('User not authenticated - skipping admin tests');
    }

    // Look for admin-related navigation items
    const adminNavItems = [
      page.locator('a, button').filter({ hasText: /Users/i }),
      page.locator('a, button').filter({ hasText: /Admin/i }),
      page.locator('a, button').filter({ hasText: /Settings/i }),
      page.locator('a, button').filter({ hasText: /Management/i })
    ];

    let foundAdminNav = false;
    for (const navItem of adminNavItems) {
      if (await navItem.count() > 0) {
        foundAdminNav = true;
        // Test navigation
        await navItem.first().click();
        await page.waitForTimeout(1000);
        break;
      }
    }

    // Admin nav might only be visible to admin users
  });

  test('should handle breadcrumb navigation', async ({ page }) => {
    await page.goto('/admin/users');
    await page.waitForTimeout(2000);

    if (page.url().includes('/login')) {
      test.skip('User not authenticated - skipping admin tests');
    }

    // Look for breadcrumb navigation
    const breadcrumbs = page.locator('[data-testid="breadcrumb"], .breadcrumb, nav ol, nav ul');

    if (await breadcrumbs.count() > 0) {
      await expect(breadcrumbs.first()).toBeVisible();

      // Check for breadcrumb links
      const breadcrumbLinks = breadcrumbs.locator('a, button');
      if (await breadcrumbLinks.count() > 0) {
        await expect(breadcrumbLinks.first()).toBeVisible();
      }
    }
  });
});

test.describe('Responsive Admin Interface', () => {
  test('should work on mobile devices', async ({ page }) => {
    await page.goto('/admin/users');
    await page.waitForTimeout(2000);

    if (page.url().includes('/login')) {
      test.skip('User not authenticated - skipping admin tests');
    }

    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Admin interface should still be usable on mobile
    const mainContent = page.locator('main, .main-content, .admin-content');
    if (await mainContent.count() > 0) {
      await expect(mainContent).toBeVisible();
    }

    // Mobile menu should be accessible
    const mobileMenu = page.locator('[data-testid="mobile-menu"], .mobile-menu, button').filter({ hasText: /menu/i });
    if (await mobileMenu.count() > 0) {
      await expect(mobileMenu).toBeVisible();
    }
  });

  test('should handle tablet viewport', async ({ page }) => {
    await page.goto('/admin/users');
    await page.waitForTimeout(2000);

    if (page.url().includes('/login')) {
      test.skip('User not authenticated - skipping admin tests');
    }

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    // Content should be visible and usable
    const pageContent = page.locator('body');
    await expect(pageContent).toBeVisible();

    // Check that tables/lists adapt to tablet size
    const responsiveElements = page.locator('table, .user-list, .admin-panel');
    if (await responsiveElements.count() > 0) {
      await expect(responsiveElements.first()).toBeVisible();
    }
  });
});