import { test, expect } from '@playwright/test';

test.describe('Requirements Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication - in real tests you'd handle proper login
    await page.goto('/dashboard');
  });

  test('should display dashboard layout correctly', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Dashboard - Requirements Generator/);

    // Check main header elements
    await expect(page.locator('h2')).toContainText('Welcome');

    // Check user avatar/initials
    const userAvatar = page.locator('.bg-brand-600');
    await expect(userAvatar).toBeVisible();

    // Check organization info
    const orgIcon = page.locator('[data-lucide="building"]');
    await expect(orgIcon).toBeVisible();

    // Check role badge
    const roleIcon = page.locator('[data-lucide="shield-check"]');
    await expect(roleIcon).toBeVisible();
  });

  test('should display quick actions section', async ({ page }) => {
    // Check Quick Actions header
    await expect(page.locator('h3')).toContainText('Quick Actions');

    // Check all four quick action cards
    const quickActions = [
      { icon: 'file-plus', title: 'New Project', description: 'Start requirements gathering' },
      { icon: 'upload', title: 'Import Documents', description: 'Upload existing requirements' },
      { icon: 'bot', title: 'AI Assistant', description: 'Get intelligent suggestions' },
      { icon: 'users', title: 'Team Collaboration', description: 'Invite team members' }
    ];

    for (const action of quickActions) {
      const actionCard = page.locator('.relative.rounded-lg.border').filter({
        hasText: action.title
      });
      await expect(actionCard).toBeVisible();
      await expect(actionCard.locator(`[data-lucide="${action.icon}"]`)).toBeVisible();
      await expect(actionCard).toContainText(action.description);
    }
  });

  test('should have hoverable quick action cards', async ({ page }) => {
    const newProjectCard = page.locator('.relative.rounded-lg.border').first();

    // Check hover effect (shadow change)
    await expect(newProjectCard).toHaveClass(/hover:shadow-md/);
    await expect(newProjectCard).toHaveClass(/cursor-pointer/);
  });

  test('should display recent projects section', async ({ page }) => {
    // Check Recent Projects header
    const recentProjectsHeader = page.locator('h3').filter({ hasText: 'Recent Projects' });
    await expect(recentProjectsHeader).toBeVisible();

    // Check "View all" link
    const viewAllLink = page.locator('a').filter({ hasText: 'View all' });
    await expect(viewAllLink).toBeVisible();

    // Check empty state
    const emptyState = page.locator('.text-center.py-12');
    await expect(emptyState).toBeVisible();
    await expect(emptyState.locator('[data-lucide="folder"]')).toBeVisible();
    await expect(emptyState).toContainText('No projects yet');
    await expect(emptyState).toContainText('Get started by creating your first requirements project');

    // Check "New Project" button in empty state
    const newProjectBtn = emptyState.locator('button').filter({ hasText: 'New Project' });
    await expect(newProjectBtn).toBeVisible();
    await expect(newProjectBtn.locator('[data-lucide="plus"]')).toBeVisible();
  });

  test('should display statistics overview', async ({ page }) => {
    // Check all three stat cards
    const statCards = [
      { icon: 'file-text', title: 'Total Requirements', value: '0' },
      { icon: 'users', title: 'Team Members', value: '1' },
      { icon: 'activity', title: 'Active Projects', value: '0' }
    ];

    for (const stat of statCards) {
      const statCard = page.locator('.bg-white.overflow-hidden.shadow.rounded-lg').filter({
        hasText: stat.title
      });

      await expect(statCard).toBeVisible();
      await expect(statCard.locator(`[data-lucide="${stat.icon}"]`)).toBeVisible();
      await expect(statCard.locator('dt')).toContainText(stat.title);
      await expect(statCard.locator('dd')).toContainText(stat.value);
    }
  });

  test('should have working navigation elements', async ({ page }) => {
    // Test Profile button
    const profileBtn = page.locator('a[href="/profile"]');
    await expect(profileBtn).toBeVisible();
    await expect(profileBtn).toContainText('Profile');
    await expect(profileBtn.locator('[data-lucide="user"]')).toBeVisible();

    // Test Manage Users button (if visible for admin users)
    const manageUsersBtn = page.locator('a[href="/admin/users"]');
    if (await manageUsersBtn.count() > 0) {
      await expect(manageUsersBtn).toBeVisible();
      await expect(manageUsersBtn).toContainText('Manage Users');
      await expect(manageUsersBtn.locator('[data-lucide="users"]')).toBeVisible();
    }
  });

  test('should have responsive grid layout', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 });

    // Quick actions should be in 4 columns on large screens
    const quickActionsGrid = page.locator('.grid.grid-cols-1.gap-4.sm\\:grid-cols-2.lg\\:grid-cols-4');
    await expect(quickActionsGrid).toBeVisible();

    // Stats should be in 3 columns on large screens
    const statsGrid = page.locator('.grid.grid-cols-1.gap-4.sm\\:grid-cols-2.lg\\:grid-cols-3');
    await expect(statsGrid).toBeVisible();

    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(quickActionsGrid).toBeVisible();
    await expect(statsGrid).toBeVisible();

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(quickActionsGrid).toBeVisible();
    await expect(statsGrid).toBeVisible();
  });

  test('should load and display all Lucide icons', async ({ page }) => {
    // Wait for Lucide icons to initialize
    await page.waitForFunction(() => window.lucide);

    const expectedIcons = [
      'layers', 'building', 'shield-check', 'user', 'users',
      'file-plus', 'upload', 'bot', 'folder', 'plus',
      'file-text', 'activity'
    ];

    for (const iconName of expectedIcons) {
      const icon = page.locator(`[data-lucide="${iconName}"]`);
      if (await icon.count() > 0) {
        await expect(icon.first()).toBeVisible();
      }
    }
  });

  test('should handle click interactions on actionable elements', async ({ page }) => {
    // Test clicking New Project quick action
    const newProjectQuickAction = page.locator('.relative.rounded-lg.border').filter({
      hasText: 'New Project'
    });

    // Should be clickable (has cursor-pointer)
    await expect(newProjectQuickAction).toHaveClass(/cursor-pointer/);

    // Test clicking New Project button in empty state
    const newProjectButton = page.locator('button').filter({ hasText: 'New Project' });
    await expect(newProjectButton).toBeEnabled();

    // Test other quick actions are clickable
    const importDocsAction = page.locator('.relative.rounded-lg.border').filter({
      hasText: 'Import Documents'
    });
    await expect(importDocsAction).toHaveClass(/cursor-pointer/);

    const aiAssistantAction = page.locator('.relative.rounded-lg.border').filter({
      hasText: 'AI Assistant'
    });
    await expect(aiAssistantAction).toHaveClass(/cursor-pointer/);

    const teamCollabAction = page.locator('.relative.rounded-lg.border').filter({
      hasText: 'Team Collaboration'
    });
    await expect(teamCollabAction).toHaveClass(/cursor-pointer/);
  });

  test('should display proper styling and theme colors', async ({ page }) => {
    // Check brand color usage
    const brandElements = page.locator('.bg-brand-600');
    await expect(brandElements.first()).toBeVisible();

    // Check text hierarchy
    await expect(page.locator('h2')).toHaveClass(/text-2xl|text-3xl/);
    await expect(page.locator('h3')).toHaveClass(/text-lg/);

    // Check shadow and border styling
    const shadowElements = page.locator('.shadow');
    await expect(shadowElements.first()).toBeVisible();

    const borderElements = page.locator('.border');
    await expect(borderElements.first()).toBeVisible();
  });

  test('should show contextual information based on user role', async ({ page }) => {
    // Check if role is displayed
    const roleElement = page.locator('div').filter({ hasText: /Role|Admin|User/ });

    // Role should be visible in user info section
    const userInfoSection = page.locator('.flex.items-center.text-sm.text-gray-500').nth(1);
    await expect(userInfoSection).toBeVisible();
  });
});

test.describe('Dashboard Accessibility', () => {
  test('should have proper ARIA labels and semantic HTML', async ({ page }) => {
    await page.goto('/dashboard');

    // Check for proper heading hierarchy
    const h2Elements = page.locator('h2');
    await expect(h2Elements).toHaveCount(1);

    const h3Elements = page.locator('h3');
    await expect(h3Elements.first()).toBeVisible();

    // Check for proper button elements
    const buttons = page.locator('button');
    for (let i = 0; i < await buttons.count(); i++) {
      const button = buttons.nth(i);
      await expect(button).toHaveAttribute('type');
    }

    // Check for proper link elements
    const links = page.locator('a[href]');
    for (let i = 0; i < await links.count(); i++) {
      const link = links.nth(i);
      await expect(link).toHaveAttribute('href');
    }
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/dashboard');

    // Test tab navigation through interactive elements
    await page.keyboard.press('Tab');

    // Should be able to reach profile button
    const profileBtn = page.locator('a[href="/profile"]');
    await expect(profileBtn).toBeFocused();

    // Continue tabbing to reach other interactive elements
    await page.keyboard.press('Tab');

    // Should eventually reach the New Project button
    for (let i = 0; i < 10; i++) {
      const focusedElement = page.locator(':focus');
      const text = await focusedElement.textContent();
      if (text && text.includes('New Project')) {
        break;
      }
      await page.keyboard.press('Tab');
    }
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto('/dashboard');

    // Check main text elements have good contrast
    const mainHeading = page.locator('h2').first();
    await expect(mainHeading).toHaveClass(/text-gray-900/);

    const bodyText = page.locator('.text-gray-500');
    await expect(bodyText.first()).toBeVisible();

    // Check button text contrast
    const primaryButtons = page.locator('.bg-brand-600');
    await expect(primaryButtons.first()).toHaveClass(/text-white/);
  });
});