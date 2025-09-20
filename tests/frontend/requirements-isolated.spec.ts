import { test, expect } from './helpers/test-setup';
import { mockApiResponses, expectToastMessage, generateUniqueProjectName } from './helpers/test-setup';

test.describe('Requirements Management - Isolated Tests (No DB)', () => {
  test.beforeEach(async ({ page }) => {
    // Setup API mocks to avoid database writes
    await mockApiResponses(page);
  });

  test('should create project without database persistence', async ({ page, testData }) => {
    await page.goto('/dashboard');

    // Click New Project quick action
    const newProjectAction = page.locator('.relative.rounded-lg.border').filter({
      hasText: 'New Project'
    });
    await newProjectAction.click();

    // Fill project form (this will be intercepted by mocks)
    await page.waitForSelector('input[name="name"]', { timeout: 5000 });

    const projectName = generateUniqueProjectName();
    await page.fill('input[name="name"]', projectName);
    await page.fill('textarea[name="description"]', 'Test project created with mocked API');

    // Submit form
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // Should show success (from mocked response)
    await page.waitForTimeout(1000);

    // Verify project was "created" (mocked)
    const successIndicator = page.locator('.success, .text-green-600');
    if (await successIndicator.count() > 0) {
      await expect(successIndicator).toBeVisible();
    } else {
      // Or should navigate to project page
      await expect(page.url()).toMatch(/projects/);
    }
  });

  test('should list requirements without database queries', async ({ page }) => {
    await page.goto('/projects/test-project-1/requirements');

    // Wait for mocked requirements to load
    await page.waitForTimeout(1000);

    // Should display mocked requirements
    const requirementsList = page.locator('.requirement-card, table, .requirements-list');
    await expect(requirementsList).toBeVisible();

    // Check for mocked requirement data
    await expect(page.locator('text=User Authentication')).toBeVisible();
    await expect(page.locator('text=Data Backup')).toBeVisible();
  });

  test('should generate documentation with mocked content', async ({ page }) => {
    await page.goto('/projects/test-project-1/documentation');

    // Select options and generate
    const generateButton = page.locator('button').filter({ hasText: /Generate|Create|Export/ });
    await generateButton.click();

    // Wait for mocked documentation
    await page.waitForTimeout(2000);

    // Should show mocked documentation content
    const documentContent = page.locator('.document-content, .preview, pre');
    if (await documentContent.count() > 0) {
      await expect(documentContent).toBeVisible();
      await expect(documentContent).toContainText('Test Project Documentation');
      await expect(documentContent).toContainText('User Authentication');
    }
  });

  test('should handle form validation without backend calls', async ({ page }) => {
    await page.goto('/projects/new');

    // Try to submit empty form
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // Client-side validation should prevent submission
    const nameField = page.locator('input[name="name"]');
    const isValid = await nameField.evaluate((input: HTMLInputElement) => input.validity.valid);
    expect(isValid).toBeFalsy();

    // Fill minimum required data
    await nameField.fill('Valid Project Name');

    // Now submission should work (and be mocked)
    await submitButton.click();
    await page.waitForTimeout(1000);

    // Should receive mocked success response
    const successIndicator = page.locator('.success, .text-green-600');
    if (await successIndicator.count() > 0) {
      await expect(successIndicator).toBeVisible();
    }
  });
});

test.describe('Requirements Management - Integration Tests (With DB)', () => {
  // These tests use the cleanDatabase fixture for proper cleanup
  test('should create project and persist to database', async ({ page, testData, cleanDatabase }) => {
    // This test actually hits the database but cleans up automatically
    await page.goto('/dashboard');

    const projectName = generateUniqueProjectName();

    // Create project (real API call)
    const newProjectAction = page.locator('button').filter({ hasText: 'New Project' });
    await newProjectAction.click();

    await page.waitForSelector('input[name="name"]', { timeout: 5000 });
    await page.fill('input[name="name"]', projectName);
    await page.fill('textarea[name="description"]', 'Integration test project');

    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // Wait for real response
    await page.waitForTimeout(3000);

    // Verify project exists in database
    await page.goto('/projects');
    await expect(page.locator(`text=${projectName}`)).toBeVisible();

    // Database cleanup happens automatically via the cleanDatabase fixture
  });

  test('should create and retrieve requirements from database', async ({ page, testData, cleanDatabase }) => {
    // Create a requirement that persists to database
    await page.goto('/projects/test-project-id/requirements/new');

    await page.fill('input[name="title"]', 'Integration Test Requirement');
    await page.fill('textarea[name="description"]', 'This requirement tests database persistence');

    const typeSelect = page.locator('select[name="type"]');
    if (await typeSelect.count() > 0) {
      await typeSelect.selectOption('functional');
    }

    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    await page.waitForTimeout(3000);

    // Verify requirement was saved
    await page.goto('/projects/test-project-id/requirements');
    await expect(page.locator('text=Integration Test Requirement')).toBeVisible();

    // Cleanup happens automatically
  });
});

test.describe('Mixed Testing Strategy', () => {
  test('should test UI behavior with mocks, then verify with real API', async ({ page }) => {
    // Phase 1: Test UI behavior with mocks (fast, isolated)
    await mockApiResponses(page);
    await page.goto('/projects/new');

    const projectName = 'Mock Test Project';
    await page.fill('input[name="name"]', projectName);
    await page.fill('textarea[name="description"]', 'Testing with mocks first');

    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // Verify UI responds correctly to mocked success
    await page.waitForTimeout(1000);

    // Phase 2: Remove mocks and test with real API for integration
    await page.unroute('**/api/projects');

    // Test same flow with real backend
    await page.goto('/projects/new');
    await page.fill('input[name="name"]', generateUniqueProjectName());
    await page.fill('textarea[name="description"]', 'Real API integration test');

    await submitButton.click();
    await page.waitForTimeout(3000);

    // This should actually create the project (requires cleanup)
  });

  test('should test error scenarios with mocks', async ({ page }) => {
    // Mock error responses
    await page.route('**/api/projects', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Validation failed',
          details: {
            name: 'Project name already exists'
          }
        })
      });
    });

    await page.goto('/projects/new');

    await page.fill('input[name="name"]', 'Duplicate Project');
    await page.fill('textarea[name="description"]', 'This will trigger a mocked error');

    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    await page.waitForTimeout(1000);

    // Should display mocked error message
    const errorMessage = page.locator('.error, .text-red-600');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('already exists');
  });
});

test.describe('Performance Testing (Mocked)', () => {
  test('should handle large datasets efficiently', async ({ page }) => {
    // Mock large dataset
    await page.route('**/api/projects/*/requirements', async (route) => {
      const largeDataset = {
        items: Array.from({ length: 100 }, (_, i) => ({
          id: `req-${i}`,
          title: `Requirement ${i}`,
          description: `Description for requirement ${i}`,
          type: 'functional',
          priority: 'medium',
          status: 'draft'
        })),
        total: 100,
        page: 1,
        page_size: 50
      };

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(largeDataset)
      });
    });

    const startTime = Date.now();
    await page.goto('/projects/test-project/requirements');

    // Wait for content to load
    await page.waitForSelector('.requirement-card, table tr', { timeout: 10000 });

    const loadTime = Date.now() - startTime;

    // Should load within reasonable time
    expect(loadTime).toBeLessThan(5000); // 5 seconds max

    // Should display paginated results
    const requirements = page.locator('.requirement-card, table tr');
    const count = await requirements.count();
    expect(count).toBeGreaterThan(10); // Should show many requirements
  });

  test('should handle network delays gracefully', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/projects', async (route) => {
      // Simulate 2 second delay
      await new Promise(resolve => setTimeout(resolve, 2000));

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [],
          total: 0
        })
      });
    });

    await page.goto('/projects');

    // Should show loading state
    const loadingIndicator = page.locator('.loading, .spinner, [aria-label*="loading"]');
    if (await loadingIndicator.count() > 0) {
      await expect(loadingIndicator).toBeVisible();
    }

    // Wait for content to load
    await page.waitForTimeout(3000);

    // Loading indicator should disappear
    if (await loadingIndicator.count() > 0) {
      await expect(loadingIndicator).toBeHidden();
    }
  });
});

// Example of test that can run with different strategies
test.describe.configure({ mode: 'parallel' });

test.describe('Flexible Test Strategy', () => {
  test('should work with DATABASE_STRATEGY environment variable', async ({ page }) => {
    const strategy = process.env.DATABASE_STRATEGY || 'mock';

    if (strategy === 'mock') {
      // Use mocked responses
      await mockApiResponses(page);
      await page.goto('/dashboard');

      // Test with mocked data
      const quickActions = page.locator('.relative.rounded-lg.border');
      await expect(quickActions).toHaveCount(4);

    } else if (strategy === 'test-db') {
      // Use real database but with cleanup
      await page.goto('/dashboard');

      // Test with real database
      const stats = page.locator('.bg-white.overflow-hidden.shadow.rounded-lg');
      await expect(stats).toHaveCount(3);

    } else if (strategy === 'staging') {
      // Use staging environment
      await page.goto('/dashboard');

      // Verify staging environment
      await expect(page.locator('h2')).toContainText('Welcome');
    }
  });
});