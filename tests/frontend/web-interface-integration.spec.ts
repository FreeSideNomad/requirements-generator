import { test, expect } from '@playwright/test';

test.describe('Web Interface Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Login as authenticated user
    await page.goto('/login');
    await page.fill('#email', 'admin@example.com');
    await page.fill('#password', 'password123');
    await page.click('#login-button');
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test.describe('Dashboard Integration', () => {
    test('should display comprehensive dashboard with all widgets', async ({ page }) => {
      await page.goto('/dashboard');

      // Verify main dashboard sections
      await expect(page.locator('.dashboard-header')).toBeVisible();
      await expect(page.locator('.quick-stats')).toBeVisible();
      await expect(page.locator('.recent-activity')).toBeVisible();
      await expect(page.locator('.project-overview')).toBeVisible();
      await expect(page.locator('.requirements-summary')).toBeVisible();

      // Check quick stats widgets
      await expect(page.locator('.stat-total-projects')).toContainText(/\d+/);
      await expect(page.locator('.stat-total-requirements')).toContainText(/\d+/);
      await expect(page.locator('.stat-pending-approvals')).toContainText(/\d+/);
      await expect(page.locator('.stat-team-members')).toContainText(/\d+/);

      // Verify widget interactivity
      await page.click('.stat-total-projects');
      await expect(page).toHaveURL(/.*\/projects/);
    });

    test('should customize dashboard layout and widgets', async ({ page }) => {
      await page.goto('/dashboard');

      // Access dashboard customization
      await page.click('button:has-text("Customize Dashboard")');
      await expect(page.locator('.customization-panel')).toBeVisible();

      // Toggle widgets
      await page.uncheck('#widget-recent-activity');
      await page.check('#widget-ai-insights');
      await page.check('#widget-project-timeline');

      // Rearrange widgets
      await page.dragAndDrop('.widget-projects', '.widget-requirements');

      // Save customization
      await page.click('button:has-text("Save Layout")');
      await expect(page.locator('.customization-success')).toContainText('Dashboard layout saved');

      // Verify customization applied
      await page.reload();
      await expect(page.locator('#widget-ai-insights')).toBeVisible();
      await expect(page.locator('#widget-recent-activity')).not.toBeVisible();
    });

    test('should handle real-time dashboard updates', async ({ page }) => {
      await page.goto('/dashboard');

      // Monitor real-time updates
      await expect(page.locator('.real-time-indicator')).toBeVisible();

      // Simulate activity that should trigger updates
      await page.goto('/projects');
      await page.click('button:has-text("New Project")');
      await page.fill('#project-name', 'Real-time Test Project');
      await page.click('button:has-text("Create Project")');

      // Return to dashboard and verify update
      await page.goto('/dashboard');
      await expect(page.locator('.recent-activity')).toContainText('Real-time Test Project');
      await expect(page.locator('.stat-total-projects')).toContainText(/\d+/);
    });
  });

  test.describe('Navigation and Layout', () => {
    test('should navigate between all main sections seamlessly', async ({ page }) => {
      // Test main navigation
      await page.click('nav a[href="/projects"]');
      await expect(page).toHaveURL(/.*\/projects/);
      await expect(page.locator('.projects-header')).toBeVisible();

      await page.click('nav a[href="/requirements"]');
      await expect(page).toHaveURL(/.*\/requirements/);
      await expect(page.locator('.requirements-header')).toBeVisible();

      await page.click('nav a[href="/ai"]');
      await expect(page).toHaveURL(/.*\/ai/);
      await expect(page.locator('.ai-assistant-header')).toBeVisible();

      await page.click('nav a[href="/admin"]');
      await expect(page).toHaveURL(/.*\/admin/);
      await expect(page.locator('.admin-header')).toBeVisible();

      // Test breadcrumb navigation
      await page.goto('/projects/project-id/requirements');
      await expect(page.locator('.breadcrumb')).toBeVisible();
      await expect(page.locator('.breadcrumb')).toContainText('Projects > Project Name > Requirements');

      await page.click('.breadcrumb a:has-text("Projects")');
      await expect(page).toHaveURL(/.*\/projects/);
    });

    test('should handle responsive layout across different screen sizes', async ({ page }) => {
      // Test desktop layout
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/dashboard');
      await expect(page.locator('.sidebar')).toBeVisible();
      await expect(page.locator('.main-content')).toHaveCSS('margin-left', '250px');

      // Test tablet layout
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.reload();
      await expect(page.locator('.sidebar')).not.toBeVisible();
      await expect(page.locator('.mobile-menu-toggle')).toBeVisible();

      // Test mobile layout
      await page.setViewportSize({ width: 375, height: 667 });
      await page.reload();
      await expect(page.locator('.mobile-nav')).toBeVisible();
      await expect(page.locator('.main-content')).toHaveCSS('margin-left', '0px');

      // Test mobile menu functionality
      await page.click('.mobile-menu-toggle');
      await expect(page.locator('.mobile-sidebar')).toBeVisible();
    });

    test('should maintain consistent theming and branding', async ({ page }) => {
      await page.goto('/dashboard');

      // Verify brand colors and styling
      await expect(page.locator('.brand-logo')).toBeVisible();
      await expect(page.locator('body')).toHaveCSS('font-family', /Inter|system-ui/);

      // Test theme switching
      await page.click('.user-menu');
      await page.click('text=Dark Theme');
      await expect(page.locator('body')).toHaveClass(/dark-theme/);

      await page.click('.user-menu');
      await page.click('text=Light Theme');
      await expect(page.locator('body')).not.toHaveClass(/dark-theme/);

      // Verify theme persistence
      await page.reload();
      await expect(page.locator('body')).not.toHaveClass(/dark-theme/);
    });
  });

  test.describe('HTMX Dynamic Interactions', () => {
    test('should handle HTMX form submissions and updates', async ({ page }) => {
      await page.goto('/projects');

      // Test HTMX-powered project creation
      await page.click('button:has-text("New Project")');
      await expect(page.locator('.project-form')).toBeVisible();

      // Fill and submit via HTMX
      await page.fill('#project-name', 'HTMX Test Project');
      await page.fill('#project-description', 'Testing HTMX integration');
      await page.click('button[hx-post="/api/projects"]');

      // Verify HTMX response handling
      await expect(page.locator('.success-message')).toBeVisible();
      await expect(page.locator('.project-list')).toContainText('HTMX Test Project');

      // Verify no full page reload occurred
      await expect(page.locator('.htmx-indicator')).not.toBeVisible();
    });

    test('should handle HTMX live search and filtering', async ({ page }) => {
      await page.goto('/requirements');

      // Test live search with HTMX
      await page.fill('#search-requirements', 'authentication');

      // Wait for HTMX request to complete
      await expect(page.locator('.htmx-indicator')).toBeVisible();
      await expect(page.locator('.htmx-indicator')).not.toBeVisible();

      // Verify search results updated
      await expect(page.locator('.requirement-card')).toContainText(/authentication/i);

      // Test filter interactions
      await page.selectOption('#filter-priority', 'high');
      await expect(page.locator('.htmx-indicator')).toBeVisible();
      await expect(page.locator('.htmx-indicator')).not.toBeVisible();

      await expect(page.locator('.requirement-card .priority-high')).toBeVisible();
    });

    test('should handle HTMX infinite scroll and pagination', async ({ page }) => {
      await page.goto('/projects');

      // Scroll to trigger infinite scroll
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

      // Verify HTMX loading indicator
      await expect(page.locator('.loading-more')).toBeVisible();
      await expect(page.locator('.loading-more')).not.toBeVisible();

      // Verify more content loaded
      const initialProjectCount = await page.locator('.project-card').count();
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(1000);

      const newProjectCount = await page.locator('.project-card').count();
      expect(newProjectCount).toBeGreaterThan(initialProjectCount);
    });

    test('should handle HTMX modal interactions', async ({ page }) => {
      await page.goto('/requirements');

      // Open modal via HTMX
      await page.click('button[hx-get="/modals/new-requirement"]');
      await expect(page.locator('.modal')).toBeVisible();
      await expect(page.locator('.modal-content')).toContainText('New Requirement');

      // Submit form in modal
      await page.fill('#requirement-title', 'Modal Test Requirement');
      await page.click('button[hx-post="/api/requirements"]');

      // Verify modal closes and content updates
      await expect(page.locator('.modal')).not.toBeVisible();
      await expect(page.locator('.requirements-list')).toContainText('Modal Test Requirement');
    });
  });

  test.describe('Form Interactions and Validation', () => {
    test('should handle complex multi-step forms', async ({ page }) => {
      await page.goto('/projects/new');

      // Step 1: Basic Information
      await page.fill('#project-name', 'Multi-step Project');
      await page.fill('#project-description', 'Testing multi-step form flow');
      await page.selectOption('#project-type', 'web-application');
      await page.click('button:has-text("Next")');

      // Step 2: Team Configuration
      await expect(page.locator('.step-team')).toBeVisible();
      await page.fill('#team-lead', 'john.doe@example.com');
      await page.selectOption('#team-size', 'medium');
      await page.click('button:has-text("Next")');

      // Step 3: Requirements Template
      await expect(page.locator('.step-template')).toBeVisible();
      await page.click('.template-option[data-template="web-app"]');
      await page.click('button:has-text("Next")');

      // Step 4: Review and Submit
      await expect(page.locator('.step-review')).toBeVisible();
      await expect(page.locator('.review-summary')).toContainText('Multi-step Project');
      await page.click('button:has-text("Create Project")');

      // Verify project created
      await expect(page.locator('.success-message')).toContainText('Project created successfully');
      await expect(page).toHaveURL(/.*\/projects\/[a-f0-9-]+/);
    });

    test('should validate forms with real-time feedback', async ({ page }) => {
      await page.goto('/requirements/new');

      // Test required field validation
      await page.click('button:has-text("Create Requirement")');
      await expect(page.locator('.title-error')).toContainText('Title is required');

      // Test format validation
      await page.fill('#requirement-title', 'a'); // Too short
      await expect(page.locator('.title-error')).toContainText('Title must be at least 3 characters');

      await page.fill('#requirement-title', 'Valid Requirement Title');
      await expect(page.locator('.title-error')).not.toBeVisible();

      // Test email validation
      await page.fill('#stakeholder-email', 'invalid-email');
      await expect(page.locator('.email-error')).toContainText('Invalid email format');

      await page.fill('#stakeholder-email', 'valid@example.com');
      await expect(page.locator('.email-error')).not.toBeVisible();

      // Test custom validation
      await page.fill('#acceptance-criteria', 'Given When Then'); // Too simple
      await expect(page.locator('.criteria-warning')).toContainText('Consider adding more detailed criteria');
    });

    test('should handle file uploads and attachments', async ({ page }) => {
      await page.goto('/requirements/requirement-id');

      // Test file upload
      await page.click('button:has-text("Add Attachment")');
      await expect(page.locator('.file-upload-area')).toBeVisible();

      // Simulate file selection
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: 'requirements-doc.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('PDF content')
      });

      // Verify upload progress
      await expect(page.locator('.upload-progress')).toBeVisible();
      await expect(page.locator('.upload-progress')).not.toBeVisible();

      // Verify file attached
      await expect(page.locator('.attachment-list')).toContainText('requirements-doc.pdf');

      // Test file preview
      await page.click('.attachment-item .preview-button');
      await expect(page.locator('.file-preview')).toBeVisible();

      // Test file deletion
      await page.click('.attachment-item .delete-button');
      await page.click('button:has-text("Confirm Delete")');
      await expect(page.locator('.attachment-list')).not.toContainText('requirements-doc.pdf');
    });
  });

  test.describe('Search and Filter Integration', () => {
    test('should provide unified search across all content types', async ({ page }) => {
      await page.goto('/search');

      // Test global search
      await page.fill('#global-search', 'authentication');
      await page.click('button:has-text("Search")');

      // Verify search results from different content types
      await expect(page.locator('.search-results')).toBeVisible();
      await expect(page.locator('.result-projects')).toBeVisible();
      await expect(page.locator('.result-requirements')).toBeVisible();
      await expect(page.locator('.result-users')).toBeVisible();

      // Test result filtering
      await page.click('#filter-content-type-projects');
      await expect(page.locator('.result-requirements')).not.toBeVisible();
      await expect(page.locator('.result-projects')).toBeVisible();

      // Test search suggestions
      await page.fill('#global-search', 'auth'); // Partial query
      await expect(page.locator('.search-suggestions')).toBeVisible();
      await expect(page.locator('.suggestion-item')).toContainText('authentication');

      await page.click('.suggestion-item:first-child');
      await expect(page.locator('#global-search')).toHaveValue('authentication');
    });

    test('should handle advanced search with multiple criteria', async ({ page }) => {
      await page.goto('/search/advanced');

      // Configure advanced search
      await page.fill('#search-title', 'user management');
      await page.selectOption('#search-type', 'functional');
      await page.selectOption('#search-priority', 'high');
      await page.fill('#search-date-from', '2024-01-01');
      await page.fill('#search-date-to', '2024-12-31');
      await page.fill('#search-tags', 'security, authentication');

      // Execute search
      await page.click('button:has-text("Search")');

      // Verify advanced search results
      await expect(page.locator('.search-criteria-summary')).toContainText('5 filters applied');
      await expect(page.locator('.search-results')).toBeVisible();

      // Test saved searches
      await page.click('button:has-text("Save Search")');
      await page.fill('#search-name', 'Security Requirements');
      await page.click('button:has-text("Save")');

      // Verify saved search
      await expect(page.locator('.saved-searches')).toContainText('Security Requirements');

      // Test loading saved search
      await page.click('.saved-search[data-name="Security Requirements"]');
      await expect(page.locator('#search-title')).toHaveValue('user management');
      await expect(page.locator('#search-tags')).toHaveValue('security, authentication');
    });

    test('should provide contextual filtering within sections', async ({ page }) => {
      await page.goto('/projects');

      // Test project-specific filters
      await page.click('#filter-toggle');
      await expect(page.locator('.filter-panel')).toBeVisible();

      await page.selectOption('#filter-status', 'active');
      await page.selectOption('#filter-industry', 'technology');
      await page.fill('#filter-team-size-min', '5');
      await page.fill('#filter-team-size-max', '20');

      // Apply filters
      await page.click('button:has-text("Apply Filters")');

      // Verify filtered results
      await expect(page.locator('.filter-summary')).toContainText('3 filters active');
      await expect(page.locator('.project-card .status-active')).toBeVisible();

      // Test filter presets
      await page.click('button:has-text("Large Projects")');
      await expect(page.locator('.filter-preset-applied')).toContainText('Large Projects');

      // Test filter clearing
      await page.click('button:has-text("Clear All Filters")');
      await expect(page.locator('.filter-summary')).toContainText('No filters applied');
    });
  });

  test.describe('Notifications and Alerts', () => {
    test('should display and manage in-app notifications', async ({ page }) => {
      await page.goto('/dashboard');

      // Check notifications bell
      await expect(page.locator('.notifications-bell')).toBeVisible();
      await expect(page.locator('.notification-count')).toContainText(/\d+/);

      // Open notifications panel
      await page.click('.notifications-bell');
      await expect(page.locator('.notifications-panel')).toBeVisible();

      // Verify notification types
      await expect(page.locator('.notification-item')).toHaveCount.greaterThan(0);
      await expect(page.locator('.notification-type-approval')).toBeVisible();
      await expect(page.locator('.notification-type-mention')).toBeVisible();
      await expect(page.locator('.notification-type-deadline')).toBeVisible();

      // Mark notification as read
      await page.click('.notification-item:first-child .mark-read');
      await expect(page.locator('.notification-item:first-child')).not.toHaveClass(/unread/);

      // Clear all notifications
      await page.click('button:has-text("Mark All Read")');
      await expect(page.locator('.notification-count')).toContainText('0');
    });

    test('should handle toast notifications for actions', async ({ page }) => {
      await page.goto('/projects');

      // Trigger action that shows toast
      await page.click('button:has-text("New Project")');
      await page.fill('#project-name', 'Toast Test Project');
      await page.click('button:has-text("Create Project")');

      // Verify toast notification
      await expect(page.locator('.toast-notification')).toBeVisible();
      await expect(page.locator('.toast-success')).toContainText('Project created successfully');

      // Test toast auto-dismiss
      await page.waitForTimeout(5000);
      await expect(page.locator('.toast-notification')).not.toBeVisible();

      // Test error toast
      await page.route('**/api/projects', route => {
        route.fulfill({ status: 500, body: 'Server Error' });
      });

      await page.click('button:has-text("New Project")');
      await page.fill('#project-name', 'Error Test Project');
      await page.click('button:has-text("Create Project")');

      await expect(page.locator('.toast-error')).toContainText(/error|failed/i);

      // Test manual toast dismissal
      await page.click('.toast-notification .close-button');
      await expect(page.locator('.toast-notification')).not.toBeVisible();
    });

    test('should manage notification preferences', async ({ page }) => {
      await page.goto('/profile/notifications');

      // Configure notification preferences
      await expect(page.locator('.notification-settings')).toBeVisible();

      // Email notifications
      await page.check('#email-project-updates');
      await page.check('#email-requirement-approvals');
      await page.uncheck('#email-mentions');

      // In-app notifications
      await page.check('#app-deadlines');
      await page.check('#app-team-updates');
      await page.selectOption('#digest-frequency', 'daily');

      // Browser notifications
      if (await page.locator('#browser-notifications').isVisible()) {
        await page.check('#browser-notifications');
        // Handle browser permission request if needed
      }

      // Save preferences
      await page.click('button:has-text("Save Preferences")');
      await expect(page.locator('.preferences-success')).toContainText('Notification preferences saved');

      // Test notification delivery based on preferences
      await page.goto('/requirements');
      await page.click('.requirement-card:first-child .approve-button');

      // Should not get mention notification (disabled)
      await expect(page.locator('.toast-notification')).not.toContainText(/mention/i);
    });
  });

  test.describe('Keyboard Navigation and Accessibility', () => {
    test('should support keyboard navigation throughout interface', async ({ page }) => {
      await page.goto('/dashboard');

      // Test Tab navigation
      await page.keyboard.press('Tab');
      await expect(page.locator(':focus')).toHaveAttribute('href', '/projects');

      await page.keyboard.press('Tab');
      await expect(page.locator(':focus')).toHaveAttribute('href', '/requirements');

      // Test Enter key activation
      await page.keyboard.press('Enter');
      await expect(page).toHaveURL(/.*\/requirements/);

      // Test Escape key for modals
      await page.click('button:has-text("New Requirement")');
      await expect(page.locator('.modal')).toBeVisible();

      await page.keyboard.press('Escape');
      await expect(page.locator('.modal')).not.toBeVisible();

      // Test keyboard shortcuts
      await page.keyboard.press('Control+k');
      await expect(page.locator('.search-modal')).toBeVisible();

      await page.keyboard.press('Escape');
      await expect(page.locator('.search-modal')).not.toBeVisible();
    });

    test('should provide proper ARIA labels and accessibility', async ({ page }) => {
      await page.goto('/dashboard');

      // Check ARIA labels
      await expect(page.locator('.main-nav')).toHaveAttribute('role', 'navigation');
      await expect(page.locator('.main-nav')).toHaveAttribute('aria-label', 'Main navigation');

      // Check heading hierarchy
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('h2')).toBeVisible();

      // Check button accessibility
      await expect(page.locator('button:has-text("New Project")')).toHaveAttribute('aria-label');

      // Check form accessibility
      await page.goto('/projects/new');
      await expect(page.locator('#project-name')).toHaveAttribute('aria-describedby');
      await expect(page.locator('label[for="project-name"]')).toBeVisible();

      // Check skip links
      await expect(page.locator('a:has-text("Skip to main content")')).toBeVisible();
    });

    test('should support screen reader navigation', async ({ page }) => {
      await page.goto('/requirements');

      // Check landmark regions
      await expect(page.locator('main')).toHaveAttribute('role', 'main');
      await expect(page.locator('header')).toHaveAttribute('role', 'banner');
      await expect(page.locator('nav')).toHaveAttribute('role', 'navigation');

      // Check list structures
      await expect(page.locator('.requirements-list')).toHaveAttribute('role', 'list');
      await expect(page.locator('.requirement-card')).toHaveAttribute('role', 'listitem');

      // Check live regions for dynamic content
      await expect(page.locator('.search-results')).toHaveAttribute('aria-live', 'polite');
      await expect(page.locator('.notifications-panel')).toHaveAttribute('aria-live', 'assertive');
    });
  });

  test.describe('Performance and Loading States', () => {
    test('should handle loading states gracefully', async ({ page }) => {
      // Mock slow response
      await page.route('**/api/projects', route => {
        setTimeout(() => route.continue(), 2000);
      });

      await page.goto('/projects');

      // Verify loading state
      await expect(page.locator('.loading-skeleton')).toBeVisible();
      await expect(page.locator('.loading-spinner')).toBeVisible();

      // Verify content loads after delay
      await expect(page.locator('.project-card')).toBeVisible({ timeout: 5000 });
      await expect(page.locator('.loading-skeleton')).not.toBeVisible();
    });

    test('should implement progressive loading and caching', async ({ page }) => {
      await page.goto('/requirements');

      // First load - should be slower
      const startTime = Date.now();
      await expect(page.locator('.requirement-card')).toBeVisible();
      const firstLoadTime = Date.now() - startTime;

      // Navigate away and back
      await page.goto('/dashboard');
      await page.goto('/requirements');

      // Second load - should be faster due to caching
      const secondStartTime = Date.now();
      await expect(page.locator('.requirement-card')).toBeVisible();
      const secondLoadTime = Date.now() - secondStartTime;

      expect(secondLoadTime).toBeLessThan(firstLoadTime);
    });

    test('should handle network failures gracefully', async ({ page }) => {
      await page.goto('/projects');

      // Simulate network failure
      await page.route('**/api/**', route => {
        route.abort('failed');
      });

      // Try to create project
      await page.click('button:has-text("New Project")');
      await page.fill('#project-name', 'Network Test Project');
      await page.click('button:has-text("Create Project")');

      // Verify error handling
      await expect(page.locator('.network-error')).toBeVisible();
      await expect(page.locator('.retry-button')).toBeVisible();
      await expect(page.locator('.offline-indicator')).toBeVisible();

      // Test retry mechanism
      await page.unroute('**/api/**');
      await page.click('.retry-button');
      await expect(page.locator('.success-message')).toBeVisible();
    });
  });
});