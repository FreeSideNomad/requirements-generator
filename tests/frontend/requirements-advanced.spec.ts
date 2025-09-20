import { test, expect } from '@playwright/test';

test.describe('Advanced Requirements Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as authenticated user
    await page.goto('/login');
    await page.fill('#email', 'admin@example.com');
    await page.fill('#password', 'password123');
    await page.click('#login-button');
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test.describe('Enhanced Project Operations', () => {
    test('should create project with domain analysis', async ({ page }) => {
      await page.goto('/projects');
      await page.click('button:has-text("New Project")');

      // Fill project details
      await page.fill('#project-name', 'E-commerce Platform');
      await page.fill('#project-description', 'Modern e-commerce platform with microservices architecture');
      await page.selectOption('#industry-select', 'retail');

      // Enable domain analysis
      await page.check('#enable-domain-analysis');
      await page.click('button:has-text("Create Project")');

      // Verify project created with domain analysis
      await expect(page.locator('.project-card')).toContainText('E-commerce Platform');
      await expect(page.locator('.domain-analysis-badge')).toBeVisible();
    });

    test('should perform comprehensive project domain analysis', async ({ page }) => {
      // Navigate to existing project
      await page.goto('/projects');
      await page.click('.project-card:first-child');

      // Access domain analysis
      await page.click('button:has-text("Domain Analysis")');
      await expect(page).toHaveURL(/.*\/projects\/.*\/analysis/);

      // Verify domain model components
      await expect(page.locator('.domain-entities')).toBeVisible();
      await expect(page.locator('.value-objects')).toBeVisible();
      await expect(page.locator('.aggregates')).toBeVisible();
      await expect(page.locator('.bounded-contexts')).toBeVisible();

      // Check analysis results
      await expect(page.locator('.entity-card')).toHaveCount.greaterThan(0);
      await expect(page.locator('.relationship-diagram')).toBeVisible();
    });

    test('should export project documentation to markdown', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');

      // Access export functionality
      await page.click('button:has-text("Export")');
      await page.click('text=Markdown Documentation');

      // Configure export options
      await page.check('#include-dependencies');
      await page.check('#include-domain-model');
      await page.click('button:has-text("Generate Export")');

      // Verify download or display
      await expect(page.locator('.export-preview')).toBeVisible();
      await expect(page.locator('.markdown-content')).toContainText(/# Project:|## Requirements:/);
    });

    test('should view project statistics and analytics', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');

      // Navigate to statistics
      await page.click('button:has-text("Statistics")');
      await expect(page).toHaveURL(/.*\/projects\/.*\/statistics/);

      // Verify statistics dashboard
      await expect(page.locator('.stats-card')).toHaveCount.greaterThan(3);
      await expect(page.locator('.requirements-count')).toBeVisible();
      await expect(page.locator('.complexity-distribution')).toBeVisible();
      await expect(page.locator('.priority-breakdown')).toBeVisible();
      await expect(page.locator('.progress-charts')).toBeVisible();
    });
  });

  test.describe('Enhanced Requirement Operations', () => {
    test('should create requirement with domain validation', async ({ page }) => {
      // Navigate to project requirements
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Create new requirement
      await page.click('button:has-text("New Requirement")');
      await page.fill('#requirement-title', 'User Authentication Service');
      await page.fill('#requirement-description', 'Implement secure user authentication with JWT tokens');
      await page.selectOption('#requirement-type', 'functional');
      await page.selectOption('#priority', 'high');
      await page.selectOption('#complexity', 'medium');

      // Enable domain validation
      await page.check('#enable-domain-validation');
      await page.click('button:has-text("Create Requirement")');

      // Verify requirement created with auto-generated identifier
      await expect(page.locator('.requirement-card')).toContainText('User Authentication Service');
      await expect(page.locator('.requirement-id')).toContainText(/REQ-\d+/);
      await expect(page.locator('.domain-validation-status')).toContainText('Validated');
    });

    test('should view requirement with detailed relations', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Click on first requirement
      await page.click('.requirement-card:first-child');
      await expect(page).toHaveURL(/.*\/requirements\/.*\/detailed/);

      // Verify detailed view components
      await expect(page.locator('.requirement-details')).toBeVisible();
      await expect(page.locator('.related-requirements')).toBeVisible();
      await expect(page.locator('.dependency-graph')).toBeVisible();
      await expect(page.locator('.traceability-matrix')).toBeVisible();
      await expect(page.locator('.acceptance-criteria')).toBeVisible();
    });

    test('should prioritize requirements automatically', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Trigger auto-prioritization
      await page.click('button:has-text("Auto-Prioritize")');
      await expect(page.locator('.prioritization-modal')).toBeVisible();

      // Select prioritization criteria
      await page.check('#business-value');
      await page.check('#technical-complexity');
      await page.check('#risk-assessment');
      await page.click('button:has-text("Apply Prioritization")');

      // Verify requirements are re-ordered
      await expect(page.locator('.requirement-card').first()).toHaveClass(/priority-high/);
      await expect(page.locator('.prioritization-explanation')).toBeVisible();
    });

    test('should analyze requirement dependencies', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Access dependency analysis
      await page.click('button:has-text("Analyze Dependencies")');
      await expect(page).toHaveURL(/.*\/requirements\/dependencies/);

      // Verify dependency visualization
      await expect(page.locator('.dependency-graph')).toBeVisible();
      await expect(page.locator('.dependency-matrix')).toBeVisible();
      await expect(page.locator('.circular-dependency-warning')).toBeVisible();

      // Check dependency relationships
      await expect(page.locator('.dependency-edge')).toHaveCount.greaterThan(0);
      await expect(page.locator('.dependency-strength')).toBeVisible();
    });

    test('should perform batch requirement operations', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Select multiple requirements
      await page.check('.requirement-checkbox:nth-child(1)');
      await page.check('.requirement-checkbox:nth-child(2)');
      await page.check('.requirement-checkbox:nth-child(3)');

      // Access batch operations
      await page.click('button:has-text("Batch Operations")');
      await expect(page.locator('.batch-menu')).toBeVisible();

      // Test batch priority update
      await page.click('text=Update Priority');
      await page.selectOption('#batch-priority', 'high');
      await page.click('button:has-text("Apply to Selected")');

      // Verify batch update applied
      await expect(page.locator('.requirement-card.selected .priority-badge')).toHaveText('High');
    });
  });

  test.describe('Advanced Quality Management', () => {
    test('should validate requirement quality with detailed metrics', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');
      await page.click('.requirement-card:first-child');

      // Trigger quality analysis
      await page.click('button:has-text("Quality Analysis")');
      await expect(page.locator('.quality-panel')).toBeVisible();

      // Verify quality metrics
      await expect(page.locator('.clarity-score')).toBeVisible();
      await expect(page.locator('.completeness-score')).toBeVisible();
      await expect(page.locator('.testability-score')).toBeVisible();
      await expect(page.locator('.consistency-score')).toBeVisible();

      // Check quality recommendations
      await expect(page.locator('.quality-recommendations')).toBeVisible();
      await expect(page.locator('.improvement-suggestions')).toContainText(/improve|enhance|clarify/i);
    });

    test('should generate acceptance criteria with quality validation', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');
      await page.click('.requirement-card:first-child');

      // Generate acceptance criteria
      await page.click('button:has-text("Generate Acceptance Criteria")');
      await expect(page.locator('.criteria-generation-panel')).toBeVisible();

      // Select criteria types
      await page.check('#scenario-based');
      await page.check('#rule-based');
      await page.check('#example-based');
      await page.click('button:has-text("Generate")');

      // Verify generated criteria
      await expect(page.locator('.acceptance-criteria-list')).toBeVisible();
      await expect(page.locator('.criteria-item')).toHaveCount.greaterThan(2);
      await expect(page.locator('.criteria-validation-status')).toContainText('Valid');

      // Test criteria editing
      await page.click('.criteria-item:first-child .edit-button');
      await page.fill('.criteria-edit-input', 'Given a user with valid credentials...');
      await page.click('button:has-text("Save")');
    });

    test('should perform comprehensive project quality analysis', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');

      // Access project-wide quality analysis
      await page.click('button:has-text("Quality Dashboard")');
      await expect(page).toHaveURL(/.*\/projects\/.*\/quality/);

      // Verify quality dashboard components
      await expect(page.locator('.overall-quality-score')).toBeVisible();
      await expect(page.locator('.quality-trends-chart')).toBeVisible();
      await expect(page.locator('.requirement-quality-distribution')).toBeVisible();
      await expect(page.locator('.quality-issues-list')).toBeVisible();

      // Check quality alerts
      await expect(page.locator('.quality-alert')).toBeVisible();
      await expect(page.locator('.improvement-roadmap')).toBeVisible();
    });
  });

  test.describe('Enhanced Filtering and Search', () => {
    test('should perform advanced requirement filtering', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Open advanced filters
      await page.click('button:has-text("Advanced Filters")');
      await expect(page.locator('.advanced-filter-panel')).toBeVisible();

      // Apply multiple filters
      await page.selectOption('#filter-type', 'functional');
      await page.selectOption('#filter-priority', 'high');
      await page.selectOption('#filter-status', 'approved');
      await page.fill('#filter-date-from', '2024-01-01');
      await page.fill('#filter-date-to', '2024-12-31');

      // Apply filters
      await page.click('button:has-text("Apply Filters")');

      // Verify filtered results
      await expect(page.locator('.filter-summary')).toContainText('3 filters applied');
      await expect(page.locator('.requirement-card')).toHaveCount.greaterThan(0);

      // Test filter presets
      await page.click('button:has-text("Critical Requirements")');
      await expect(page.locator('.preset-applied')).toContainText('Critical Requirements');
    });

    test('should search requirements with fuzzy matching', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Test fuzzy search
      await page.fill('#search-input', 'authenticaton'); // Intentional typo
      await page.click('button:has-text("Search")');

      // Verify fuzzy matching works
      await expect(page.locator('.search-results')).toBeVisible();
      await expect(page.locator('.search-suggestion')).toContainText('Did you mean: authentication?');
      await expect(page.locator('.requirement-card')).toContainText(/authentication/i);

      // Test search filters
      await page.click('#search-type-functional');
      await page.click('#search-in-descriptions');
      await page.click('button:has-text("Refine Search")');
    });

    test('should save and load custom filter presets', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Create custom filter
      await page.click('button:has-text("Advanced Filters")');
      await page.selectOption('#filter-priority', 'high');
      await page.selectOption('#filter-complexity', 'medium');
      await page.fill('#filter-tags', 'security,authentication');

      // Save as preset
      await page.click('button:has-text("Save as Preset")');
      await page.fill('#preset-name', 'Security Features');
      await page.fill('#preset-description', 'High priority security-related requirements');
      await page.click('button:has-text("Save Preset")');

      // Clear filters and test preset loading
      await page.click('button:has-text("Clear All")');
      await page.click('button:has-text("Load Preset")');
      await page.click('text=Security Features');

      // Verify preset loaded correctly
      await expect(page.locator('#filter-priority')).toHaveValue('high');
      await expect(page.locator('#filter-complexity')).toHaveValue('medium');
    });
  });

  test.describe('Integration and Collaboration Features', () => {
    test('should handle real-time collaborative editing', async ({ page, context }) => {
      // Open requirement in first tab
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');
      await page.click('.requirement-card:first-child');

      // Simulate second user (new page)
      const page2 = await context.newPage();
      await page2.goto('/login');
      await page2.fill('#email', 'user@example.com');
      await page2.fill('#password', 'password123');
      await page2.click('#login-button');

      // Navigate to same requirement
      await page2.goto(page.url());

      // Edit in first tab
      await page.click('button:has-text("Edit")');
      await page.fill('#requirement-description', 'Updated requirement description by user 1');

      // Verify real-time update in second tab
      await expect(page2.locator('.live-update-indicator')).toBeVisible();
      await expect(page2.locator('.collaborative-cursor')).toBeVisible();

      // Save changes
      await page.click('button:has-text("Save")');
      await expect(page2.locator('#requirement-description')).toContainText('Updated requirement description by user 1');
    });

    test('should manage requirement versioning and history', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');
      await page.click('.requirement-card:first-child');

      // Edit requirement multiple times
      await page.click('button:has-text("Edit")');
      await page.fill('#requirement-description', 'Version 1 of requirement');
      await page.click('button:has-text("Save")');

      await page.click('button:has-text("Edit")');
      await page.fill('#requirement-description', 'Version 2 of requirement');
      await page.click('button:has-text("Save")');

      // Access version history
      await page.click('button:has-text("Version History")');
      await expect(page.locator('.version-history-panel')).toBeVisible();

      // Verify version list
      await expect(page.locator('.version-item')).toHaveCount(3); // Original + 2 edits
      await expect(page.locator('.version-item:first-child')).toContainText('Version 2');

      // Test version comparison
      await page.click('.version-item:nth-child(2) .compare-button');
      await expect(page.locator('.version-diff')).toBeVisible();
      await expect(page.locator('.diff-added')).toContainText('Version 2');
      await expect(page.locator('.diff-removed')).toContainText('Version 1');

      // Test rollback
      await page.click('.version-item:nth-child(2) .rollback-button');
      await page.click('button:has-text("Confirm Rollback")');
      await expect(page.locator('#requirement-description')).toContainText('Version 1 of requirement');
    });

    test('should handle requirement templates and replication', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Create requirement from template
      await page.click('button:has-text("New from Template")');
      await expect(page.locator('.template-selector')).toBeVisible();

      // Select template category
      await page.click('.template-category[data-category="user-management"]');
      await page.click('.template-item:has-text("User Registration")');

      // Customize template
      await page.fill('#requirement-title', 'Custom User Registration');
      await page.fill('#project-specific-field', 'Mobile app registration');
      await page.click('button:has-text("Create from Template")');

      // Verify requirement created with template structure
      await expect(page.locator('.requirement-card')).toContainText('Custom User Registration');
      await expect(page.locator('.template-badge')).toContainText('User Registration Template');

      // Test saving as new template
      await page.click('.requirement-card:first-child');
      await page.click('button:has-text("Save as Template")');
      await page.fill('#template-name', 'Mobile Registration Template');
      await page.selectOption('#template-category', 'mobile-apps');
      await page.click('button:has-text("Save Template")');
    });
  });

  test.describe('Performance and Error Handling', () => {
    test('should handle large requirement datasets efficiently', async ({ page }) => {
      // Navigate to project with many requirements
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Test virtual scrolling/pagination
      await expect(page.locator('.requirement-card')).toHaveCount.greaterThan(0);
      await expect(page.locator('.pagination-info')).toBeVisible();

      // Test performance with large dataset operations
      await page.click('button:has-text("Select All")');
      await page.click('button:has-text("Batch Operations")');

      // Verify UI remains responsive
      await expect(page.locator('.batch-operation-progress')).toBeVisible();
      await expect(page.locator('.performance-indicator')).toContainText(/\d+ms/);
    });

    test('should recover from network errors gracefully', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');

      // Simulate network error
      await page.route('**/api/v2/requirements/**', route => {
        route.fulfill({ status: 500, body: 'Server Error' });
      });

      // Try to create requirement
      await page.click('button:has-text("New Requirement")');
      await page.fill('#requirement-title', 'Test Requirement');
      await page.click('button:has-text("Create Requirement")');

      // Verify error handling
      await expect(page.locator('.error-message')).toContainText(/network error|server error/i);
      await expect(page.locator('button:has-text("Retry")')).toBeVisible();
      await expect(page.locator('button:has-text("Save Locally")')).toBeVisible();

      // Test retry mechanism
      await page.unroute('**/api/v2/requirements/**');
      await page.click('button:has-text("Retry")');
      await expect(page.locator('.success-message')).toBeVisible();
    });

    test('should handle concurrent editing conflicts', async ({ page, context }) => {
      // Set up conflict scenario
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      await page.click('text=Requirements');
      await page.click('.requirement-card:first-child');

      // Simulate concurrent edit
      const page2 = await context.newPage();
      await page2.goto(page.url());

      // Both users start editing
      await page.click('button:has-text("Edit")');
      await page2.click('button:has-text("Edit")');

      // First user saves
      await page.fill('#requirement-description', 'Edit by user 1');
      await page.click('button:has-text("Save")');

      // Second user tries to save
      await page2.fill('#requirement-description', 'Edit by user 2');
      await page2.click('button:has-text("Save")');

      // Verify conflict resolution UI
      await expect(page2.locator('.merge-conflict-dialog')).toBeVisible();
      await expect(page2.locator('.conflict-options')).toBeVisible();

      // Test merge resolution
      await page2.click('button:has-text("Merge Changes")');
      await expect(page2.locator('.merge-preview')).toBeVisible();
      await page2.click('button:has-text("Apply Merge")');
    });
  });
});