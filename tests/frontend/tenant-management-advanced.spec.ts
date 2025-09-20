import { test, expect } from '@playwright/test';

test.describe('Enterprise Tenant Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin user with tenant management permissions
    await page.goto('/login');
    await page.fill('#email', 'admin@example.com');
    await page.fill('#password', 'password123');
    await page.click('#login-button');
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test.describe('Tenant CRUD Operations', () => {
    test('should create new tenant with industry template', async ({ page }) => {
      await page.goto('/admin/tenants');

      // Create new tenant
      await page.click('button:has-text("New Tenant")');
      await expect(page.locator('.tenant-creation-modal')).toBeVisible();

      // Fill tenant details
      await page.fill('#tenant-name', 'Acme Corporation');
      await page.fill('#tenant-subdomain', 'acme-corp');
      await page.selectOption('#industry-select', 'technology');
      await page.selectOption('#subscription-tier', 'enterprise');
      await page.fill('#max-users', '500');
      await page.fill('#max-projects', '100');

      // Configure industry template
      await page.check('#apply-industry-template');
      await expect(page.locator('.template-preview')).toBeVisible();
      await expect(page.locator('.template-features')).toContainText(/project templates|requirement categories|workflow templates/i);

      // Create tenant
      await page.click('button:has-text("Create Tenant")');

      // Verify tenant created
      await expect(page.locator('.success-message')).toContainText('Tenant created successfully');
      await expect(page.locator('.tenant-card')).toContainText('Acme Corporation');
      await expect(page.locator('.subdomain-link')).toContainText('acme-corp');
    });

    test('should list tenants with filtering and pagination', async ({ page }) => {
      await page.goto('/admin/tenants');

      // Test basic tenant listing
      await expect(page.locator('.tenant-card')).toHaveCount.greaterThan(0);
      await expect(page.locator('.pagination-controls')).toBeVisible();

      // Test filtering by status
      await page.click('#filter-status');
      await page.selectOption('#filter-status', 'active');
      await page.click('button:has-text("Apply Filter")');
      await expect(page.locator('.tenant-card .status-active')).toHaveCount.greaterThan(0);

      // Test filtering by industry
      await page.selectOption('#filter-industry', 'technology');
      await page.click('button:has-text("Apply Filter")');
      await expect(page.locator('.filter-summary')).toContainText('2 filters applied');

      // Test search functionality
      await page.fill('#search-tenants', 'acme');
      await page.click('button:has-text("Search")');
      await expect(page.locator('.tenant-card')).toContainText(/acme/i);

      // Test pagination
      await page.click('button:has-text("Next Page")');
      await expect(page.locator('.page-indicator')).toContainText('Page 2');
    });

    test('should view detailed tenant information', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');
      await expect(page).toHaveURL(/.*\/admin\/tenants\/[a-f0-9-]+/);

      // Verify tenant details sections
      await expect(page.locator('.tenant-overview')).toBeVisible();
      await expect(page.locator('.subscription-details')).toBeVisible();
      await expect(page.locator('.usage-statistics')).toBeVisible();
      await expect(page.locator('.user-list')).toBeVisible();
      await expect(page.locator('.project-summary')).toBeVisible();

      // Check usage metrics
      await expect(page.locator('.users-count')).toContainText(/\d+/);
      await expect(page.locator('.projects-count')).toContainText(/\d+/);
      await expect(page.locator('.storage-usage')).toContainText(/MB|GB/);

      // Verify configuration settings
      await expect(page.locator('.tenant-settings')).toBeVisible();
      await expect(page.locator('.feature-flags')).toBeVisible();
    });

    test('should update tenant configuration', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');

      // Edit tenant details
      await page.click('button:has-text("Edit Tenant")');
      await expect(page.locator('.edit-tenant-form')).toBeVisible();

      // Update basic information
      await page.fill('#tenant-name', 'Updated Tenant Name');
      await page.fill('#tenant-description', 'Updated description for testing');

      // Update subscription limits
      await page.fill('#max-users', '750');
      await page.fill('#max-projects', '150');
      await page.selectOption('#subscription-tier', 'premium');

      // Save changes
      await page.click('button:has-text("Save Changes")');

      // Verify update
      await expect(page.locator('.success-message')).toContainText('Tenant updated successfully');
      await expect(page.locator('.tenant-name')).toContainText('Updated Tenant Name');
      await expect(page.locator('.subscription-tier')).toContainText('Premium');
    });

    test('should delete/deactivate tenant', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');

      // Initiate tenant deletion
      await page.click('button:has-text("Delete Tenant")');
      await expect(page.locator('.delete-confirmation-modal')).toBeVisible();

      // Verify deletion warning
      await expect(page.locator('.deletion-warning')).toContainText(/permanent|irreversible|data loss/i);
      await expect(page.locator('.affected-resources')).toBeVisible();

      // Choose deactivation instead
      await page.click('button:has-text("Deactivate Instead")');
      await page.fill('#deactivation-reason', 'Testing deactivation workflow');
      await page.click('button:has-text("Confirm Deactivation")');

      // Verify deactivation
      await expect(page.locator('.success-message')).toContainText('Tenant deactivated');
      await expect(page.locator('.tenant-status')).toContainText('Suspended');
    });
  });

  test.describe('Tenant Subdomain Management', () => {
    test('should access tenant by subdomain', async ({ page }) => {
      // Test subdomain routing
      await page.goto('/admin/tenants');
      const subdomainElement = page.locator('.tenant-card:first-child .subdomain-link');
      const subdomain = await subdomainElement.textContent();

      // Click subdomain link
      await subdomainElement.click();

      // Verify tenant-specific interface
      await expect(page.locator('.tenant-branding')).toBeVisible();
      await expect(page.locator('.tenant-logo')).toBeVisible();
      await expect(page.locator('.tenant-specific-navigation')).toBeVisible();

      // Check tenant isolation
      await expect(page.locator('[data-tenant-id]')).toBeVisible();
    });

    test('should validate subdomain uniqueness', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('button:has-text("New Tenant")');

      // Try to use existing subdomain
      await page.fill('#tenant-subdomain', 'existing-tenant');
      await page.click('#validate-subdomain');

      // Verify validation error
      await expect(page.locator('.subdomain-error')).toContainText('Subdomain already exists');
      await expect(page.locator('.subdomain-suggestions')).toBeVisible();

      // Test subdomain format validation
      await page.fill('#tenant-subdomain', 'invalid@subdomain!');
      await expect(page.locator('.format-error')).toContainText(/invalid format|alphanumeric/i);

      // Use valid subdomain
      await page.fill('#tenant-subdomain', 'valid-subdomain-123');
      await page.click('#validate-subdomain');
      await expect(page.locator('.subdomain-success')).toContainText('Subdomain available');
    });

    test('should handle custom domain configuration', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');

      // Access domain settings
      await page.click('button:has-text("Domain Settings")');
      await expect(page.locator('.domain-configuration')).toBeVisible();

      // Add custom domain
      await page.fill('#custom-domain', 'requirements.acme.com');
      await page.click('button:has-text("Add Domain")');

      // Verify domain validation process
      await expect(page.locator('.domain-verification')).toBeVisible();
      await expect(page.locator('.dns-instructions')).toContainText(/CNAME|DNS/i);
      await expect(page.locator('.verification-status')).toContainText('Pending Verification');

      // Test SSL certificate configuration
      await page.check('#enable-ssl');
      await expect(page.locator('.ssl-options')).toBeVisible();
      await page.selectOption('#ssl-provider', 'lets-encrypt');
    });
  });

  test.describe('Subscription and Billing Management', () => {
    test('should view tenant subscription details', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');
      await page.click('tab:has-text("Subscription")');

      // Verify subscription information
      await expect(page.locator('.current-plan')).toBeVisible();
      await expect(page.locator('.billing-cycle')).toBeVisible();
      await expect(page.locator('.next-billing-date')).toBeVisible();
      await expect(page.locator('.usage-limits')).toBeVisible();

      // Check usage metrics vs limits
      await expect(page.locator('.users-usage')).toContainText(/\d+\/\d+/);
      await expect(page.locator('.projects-usage')).toContainText(/\d+\/\d+/);
      await expect(page.locator('.storage-usage')).toContainText(/\d+/);

      // Verify billing history
      await expect(page.locator('.billing-history')).toBeVisible();
      await expect(page.locator('.invoice-item')).toHaveCount.greaterThan(0);
    });

    test('should upgrade tenant subscription', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');
      await page.click('tab:has-text("Subscription")');

      // Initiate upgrade
      await page.click('button:has-text("Upgrade Plan")');
      await expect(page.locator('.upgrade-options')).toBeVisible();

      // Select new tier
      await page.click('.plan-option[data-tier="enterprise"]');
      await page.fill('#new-max-users', '1000');
      await page.fill('#new-max-projects', '200');

      // Review upgrade
      await page.click('button:has-text("Review Upgrade")');
      await expect(page.locator('.upgrade-summary')).toBeVisible();
      await expect(page.locator('.price-change')).toContainText(/\$\d+/);
      await expect(page.locator('.feature-comparison')).toBeVisible();

      // Confirm upgrade
      await page.click('button:has-text("Confirm Upgrade")');
      await expect(page.locator('.upgrade-success')).toContainText('Subscription upgraded');
    });

    test('should check tenant resource limits', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');

      // Access limits dashboard
      await page.click('button:has-text("Resource Limits")');
      await expect(page).toHaveURL(/.*\/limits/);

      // Verify limit monitoring
      await expect(page.locator('.limits-dashboard')).toBeVisible();
      await expect(page.locator('.users-limit-chart')).toBeVisible();
      await expect(page.locator('.projects-limit-chart')).toBeVisible();
      await expect(page.locator('.storage-limit-chart')).toBeVisible();

      // Check limit alerts
      await expect(page.locator('.limit-alerts')).toBeVisible();
      await expect(page.locator('.threshold-warnings')).toBeVisible();

      // Test limit enforcement
      await page.click('button:has-text("Test Limit")');
      await expect(page.locator('.limit-test-result')).toContainText(/allowed|blocked/i);
    });

    test('should suspend and reactivate tenant', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');

      // Suspend tenant
      await page.click('button:has-text("Suspend Tenant")');
      await expect(page.locator('.suspension-modal')).toBeVisible();

      await page.selectOption('#suspension-reason', 'payment-overdue');
      await page.fill('#suspension-note', 'Payment is 30 days overdue');
      await page.click('button:has-text("Confirm Suspension")');

      // Verify suspension
      await expect(page.locator('.tenant-status')).toContainText('Suspended');
      await expect(page.locator('.suspension-banner')).toBeVisible();

      // Test tenant access restriction
      await page.goto('/projects'); // Try to access normal functionality
      await expect(page.locator('.suspended-notice')).toBeVisible();

      // Reactivate tenant
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');
      await page.click('button:has-text("Reactivate")');

      await page.fill('#reactivation-note', 'Payment received, reactivating account');
      await page.click('button:has-text("Confirm Reactivation")');

      // Verify reactivation
      await expect(page.locator('.tenant-status')).toContainText('Active');
      await expect(page.locator('.reactivation-success')).toBeVisible();
    });
  });

  test.describe('Industry Templates and Configuration', () => {
    test('should view available industry templates', async ({ page }) => {
      await page.goto('/admin/tenants/templates');

      // Verify template categories
      await expect(page.locator('.template-category')).toHaveCount.greaterThan(3);
      await expect(page.locator('.category-technology')).toBeVisible();
      await expect(page.locator('.category-healthcare')).toBeVisible();
      await expect(page.locator('.category-finance')).toBeVisible();
      await expect(page.locator('.category-retail')).toBeVisible();

      // Test template preview
      await page.click('.template-item:first-child');
      await expect(page.locator('.template-preview')).toBeVisible();
      await expect(page.locator('.template-features')).toBeVisible();
      await expect(page.locator('.sample-projects')).toBeVisible();
      await expect(page.locator('.requirement-categories')).toBeVisible();
    });

    test('should apply industry template to existing tenant', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');

      // Access template configuration
      await page.click('button:has-text("Configure Templates")');
      await expect(page.locator('.template-configuration')).toBeVisible();

      // Select new industry template
      await page.selectOption('#industry-template', 'healthcare');
      await expect(page.locator('.template-changes-preview')).toBeVisible();

      // Review template changes
      await expect(page.locator('.new-categories')).toContainText(/compliance|regulatory|patient/i);
      await expect(page.locator('.new-workflows')).toContainText(/approval|validation/i);

      // Apply template
      await page.check('#preserve-existing-data');
      await page.click('button:has-text("Apply Template")');

      // Verify template applied
      await expect(page.locator('.template-success')).toContainText('Industry template applied');
      await expect(page.locator('.active-template')).toContainText('Healthcare');
    });

    test('should customize tenant-specific configurations', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');

      // Access custom configuration
      await page.click('button:has-text("Custom Configuration")');
      await expect(page.locator('.custom-config-panel')).toBeVisible();

      // Configure feature flags
      await page.check('#enable-ai-features');
      await page.check('#enable-advanced-analytics');
      await page.uncheck('#enable-public-sharing');

      // Configure branding
      await page.fill('#tenant-logo-url', 'https://example.com/logo.png');
      await page.fill('#primary-color', '#1e40af');
      await page.fill('#secondary-color', '#64748b');

      // Configure integrations
      await page.check('#enable-slack-integration');
      await page.fill('#slack-webhook-url', 'https://hooks.slack.com/services/...');

      // Save configuration
      await page.click('button:has-text("Save Configuration")');

      // Verify configuration saved
      await expect(page.locator('.config-success')).toContainText('Configuration saved');
      await expect(page.locator('.feature-preview')).toBeVisible();
    });
  });

  test.describe('Tenant Statistics and Analytics', () => {
    test('should view comprehensive tenant statistics', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');
      await page.click('tab:has-text("Analytics")');

      // Verify analytics dashboard
      await expect(page.locator('.analytics-dashboard')).toBeVisible();
      await expect(page.locator('.usage-trends')).toBeVisible();
      await expect(page.locator('.user-activity-chart')).toBeVisible();
      await expect(page.locator('.project-statistics')).toBeVisible();
      await expect(page.locator('.feature-usage')).toBeVisible();

      // Check time period filters
      await page.selectOption('#analytics-period', 'last-30-days');
      await expect(page.locator('.chart-container')).toBeVisible();

      // Test metric details
      await page.click('.metric-card:first-child');
      await expect(page.locator('.metric-detail-modal')).toBeVisible();
      await expect(page.locator('.detailed-breakdown')).toBeVisible();
    });

    test('should export tenant data and reports', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');

      // Access export functionality
      await page.click('button:has-text("Export Data")');
      await expect(page.locator('.export-options')).toBeVisible();

      // Configure export
      await page.check('#include-users');
      await page.check('#include-projects');
      await page.check('#include-requirements');
      await page.selectOption('#export-format', 'json');
      await page.selectOption('#export-period', 'all-time');

      // Start export
      await page.click('button:has-text("Generate Export")');

      // Verify export process
      await expect(page.locator('.export-progress')).toBeVisible();
      await expect(page.locator('.export-status')).toContainText(/preparing|processing/i);

      // Check export completion
      await expect(page.locator('.download-link')).toBeVisible({ timeout: 30000 });
      await expect(page.locator('.export-size')).toContainText(/MB|KB/);
    });

    test('should monitor tenant health and performance', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');
      await page.click('tab:has-text("Health")');

      // Verify health monitoring
      await expect(page.locator('.health-dashboard')).toBeVisible();
      await expect(page.locator('.system-health-score')).toBeVisible();
      await expect(page.locator('.performance-metrics')).toBeVisible();
      await expect(page.locator('.error-rates')).toBeVisible();

      // Check health alerts
      await expect(page.locator('.health-alerts')).toBeVisible();
      await expect(page.locator('.performance-warnings')).toBeVisible();

      // Test health check
      await page.click('button:has-text("Run Health Check")');
      await expect(page.locator('.health-check-results')).toBeVisible();
      await expect(page.locator('.check-status')).toContainText(/healthy|warning|error/i);
    });
  });

  test.describe('Multi-tenant Security and Isolation', () => {
    test('should verify tenant data isolation', async ({ page }) => {
      // Login to first tenant
      await page.goto('/login');
      await page.fill('#email', 'user1@tenant1.com');
      await page.fill('#password', 'password123');
      await page.click('#login-button');

      // Access tenant-specific data
      await page.goto('/projects');
      const tenant1Projects = await page.locator('.project-card').count();

      // Switch to different tenant
      await page.goto('/admin/tenants');
      await page.click('.tenant-switch[data-tenant="tenant2"]');

      // Verify data isolation
      await page.goto('/projects');
      const tenant2Projects = await page.locator('.project-card').count();

      // Ensure different data sets
      expect(tenant1Projects).not.toBe(tenant2Projects);
      await expect(page.locator('[data-tenant-id="tenant2"]')).toBeVisible();
    });

    test('should handle cross-tenant access attempts', async ({ page }) => {
      // Try to access another tenant's data directly
      await page.goto('/projects/tenant2-project-id');

      // Verify access denied
      await expect(page.locator('.access-denied')).toBeVisible();
      await expect(page.locator('.security-warning')).toContainText(/unauthorized|access denied/i);

      // Check security audit log
      await page.goto('/admin/security-logs');
      await expect(page.locator('.security-event')).toContainText('Unauthorized access attempt');
    });

    test('should manage tenant-specific user roles', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');
      await page.click('tab:has-text("Users")');

      // View tenant users
      await expect(page.locator('.tenant-users-list')).toBeVisible();
      await expect(page.locator('.user-row')).toHaveCount.greaterThan(0);

      // Edit user role
      await page.click('.user-row:first-child .edit-role-button');
      await expect(page.locator('.role-editor')).toBeVisible();

      await page.selectOption('#user-role', 'project-manager');
      await page.check('#can-create-projects');
      await page.check('#can-approve-requirements');
      await page.click('button:has-text("Update Role")');

      // Verify role updated
      await expect(page.locator('.role-success')).toContainText('User role updated');
      await expect(page.locator('.user-role-badge')).toContainText('Project Manager');
    });
  });

  test.describe('Error Handling and Edge Cases', () => {
    test('should handle tenant creation failures gracefully', async ({ page }) => {
      // Mock server error
      await page.route('**/api/tenants', route => {
        route.fulfill({ status: 500, body: 'Server Error' });
      });

      await page.goto('/admin/tenants');
      await page.click('button:has-text("New Tenant")');

      // Fill form and submit
      await page.fill('#tenant-name', 'Test Tenant');
      await page.fill('#tenant-subdomain', 'test-tenant');
      await page.click('button:has-text("Create Tenant")');

      // Verify error handling
      await expect(page.locator('.error-message')).toContainText(/server error|failed to create/i);
      await expect(page.locator('button:has-text("Retry")')).toBeVisible();
      await expect(page.locator('.form-data-preserved')).toBeVisible();
    });

    test('should handle database connection issues', async ({ page }) => {
      // Mock database error
      await page.route('**/api/tenants/**', route => {
        route.fulfill({ status: 503, body: 'Database Unavailable' });
      });

      await page.goto('/admin/tenants');

      // Verify error handling
      await expect(page.locator('.service-unavailable')).toBeVisible();
      await expect(page.locator('.retry-mechanism')).toBeVisible();
      await expect(page.locator('.status-indicator')).toContainText('Service Unavailable');
    });

    test('should handle concurrent tenant modifications', async ({ page, context }) => {
      // Setup concurrent editing scenario
      await page.goto('/admin/tenants');
      await page.click('.tenant-card:first-child');

      // Second admin user
      const page2 = await context.newPage();
      await page2.goto(page.url());

      // Both users edit simultaneously
      await page.click('button:has-text("Edit Tenant")');
      await page2.click('button:has-text("Edit Tenant")');

      // First user saves
      await page.fill('#tenant-name', 'Name by User 1');
      await page.click('button:has-text("Save Changes")');

      // Second user tries to save
      await page2.fill('#tenant-name', 'Name by User 2');
      await page2.click('button:has-text("Save Changes")');

      // Verify conflict resolution
      await expect(page2.locator('.conflict-resolution')).toBeVisible();
      await expect(page2.locator('.version-conflict-warning')).toContainText(/modified by another user/i);
    });
  });
});