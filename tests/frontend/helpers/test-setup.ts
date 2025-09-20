import { test as base, expect } from '@playwright/test';

// Test data interface
interface TestData {
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    role: string;
  };
  tenant: {
    id: string;
    name: string;
  };
  project: {
    id: string;
    name: string;
    description: string;
  };
}

// Extended test with database setup/teardown
export const test = base.extend<{
  authenticatedPage: typeof base;
  testData: TestData;
  cleanDatabase: void;
}>({
  // Database cleanup fixture
  cleanDatabase: [async ({ }, use) => {
    // Setup: Clean database before test
    await cleanupTestData();

    await use();

    // Teardown: Clean database after test
    await cleanupTestData();
  }, { auto: true }],

  // Pre-seeded test data
  testData: async ({ page }, use) => {
    // Create test data
    const testData = await createTestData();

    await use(testData);

    // Cleanup will be handled by cleanDatabase fixture
  },

  // Authenticated page with test user
  authenticatedPage: async ({ page, testData }, use) => {
    // Mock authentication or create real session
    await authenticateTestUser(page, testData.user);

    await use(page);
  }
});

// Mock API responses to avoid database writes
export async function mockApiResponses(page: any) {
  // Mock project creation
  await page.route('**/api/projects', async (route: any) => {
    if (route.request().method() === 'POST') {
      const requestData = await route.request().postDataJSON();

      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-project-id',
          name: requestData.name,
          description: requestData.description,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          tenant_id: 'test-tenant-id',
          created_by: 'test-user-id'
        })
      });
    } else {
      // GET requests - return mock project list
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'test-project-1',
              name: 'Test Project 1',
              description: 'A test project for UI testing'
            }
          ],
          total: 1,
          page: 1,
          page_size: 10
        })
      });
    }
  });

  // Mock requirement operations
  await page.route('**/api/projects/*/requirements', async (route: any) => {
    if (route.request().method() === 'POST') {
      const requestData = await route.request().postDataJSON();

      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-requirement-id',
          title: requestData.title,
          description: requestData.description,
          type: requestData.type || 'functional',
          priority: requestData.priority || 'medium',
          status: 'draft',
          created_at: new Date().toISOString()
        })
      });
    } else {
      // GET requests - return mock requirements
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'test-req-1',
              title: 'User Authentication',
              description: 'Users should be able to log in securely',
              type: 'functional',
              priority: 'high',
              status: 'draft'
            },
            {
              id: 'test-req-2',
              title: 'Data Backup',
              description: 'System should backup data daily',
              type: 'non_functional',
              priority: 'medium',
              status: 'approved'
            }
          ],
          total: 2,
          page: 1,
          page_size: 10
        })
      });
    }
  });

  // Mock documentation generation
  await page.route('**/api/projects/*/documentation', async (route: any) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        content: `# Test Project Documentation

## Overview
This is a test project for demonstrating requirements management.

## Requirements

### Functional Requirements
- User Authentication
- Data Management

### Non-Functional Requirements
- Performance
- Security

## Acceptance Criteria
- System should handle 100 concurrent users
- Response time < 2 seconds
        `,
        format: 'markdown',
        generated_at: new Date().toISOString()
      })
    });
  });

  // Mock authentication endpoints
  await page.route('**/api/auth/**', async (route: any) => {
    const url = route.request().url();

    if (url.includes('/login')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test-access-token',
          user: {
            id: 'test-user-id',
            email: 'test@example.com',
            first_name: 'Test',
            last_name: 'User',
            role: 'tenant_admin'
          }
        })
      });
    } else if (url.includes('/me')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-user-id',
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
          role: 'tenant_admin'
        })
      });
    }
  });
}

// Database cleanup function
async function cleanupTestData() {
  // Option 1: API cleanup calls
  try {
    const response = await fetch('http://localhost:8001/api/test/cleanup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-admin-token'
      }
    });

    if (!response.ok) {
      console.warn('Test cleanup API not available, using fallback');
    }
  } catch (error) {
    console.warn('Test cleanup failed:', error);
  }

  // Option 2: Direct database cleanup (if test database is configured)
  // This would require database connection setup
}

// Create test data
async function createTestData(): Promise<TestData> {
  return {
    user: {
      id: 'test-user-id',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      role: 'tenant_admin'
    },
    tenant: {
      id: 'test-tenant-id',
      name: 'Test Organization'
    },
    project: {
      id: 'test-project-id',
      name: 'Test Requirements Project',
      description: 'A comprehensive test project for requirements management'
    }
  };
}

// Authenticate test user
async function authenticateTestUser(page: any, user: TestData['user']) {
  // Option 1: Set authentication cookies/localStorage
  await page.addInitScript((userData) => {
    localStorage.setItem('auth_token', 'test-access-token');
    localStorage.setItem('user', JSON.stringify(userData));
  }, user);

  // Option 2: Use session-based authentication
  await page.context().addCookies([
    {
      name: 'session_id',
      value: 'test-session-id',
      domain: 'localhost',
      path: '/'
    }
  ]);
}

// Utility function to wait for HTMX requests
export async function waitForHtmxRequest(page: any, timeout = 5000) {
  await page.waitForFunction(
    () => {
      // @ts-ignore
      return window.htmx && window.htmx.logger === null;
    },
    { timeout }
  );
}

// Utility function to wait for Alpine.js
export async function waitForAlpine(page: any, timeout = 5000) {
  await page.waitForFunction(
    () => {
      // @ts-ignore
      return window.Alpine !== undefined;
    },
    { timeout }
  );
}

// Custom assertion helpers
export async function expectToastMessage(page: any, message: string) {
  const toast = page.locator('#toast-container, .toast, [role="alert"]');
  await expect(toast).toBeVisible();
  await expect(toast).toContainText(message);
}

export async function expectErrorMessage(page: any, message: string) {
  const error = page.locator('.error, .text-red-600, [role="alert"]');
  await expect(error).toBeVisible();
  await expect(error).toContainText(message);
}

export async function expectSuccessMessage(page: any, message: string) {
  const success = page.locator('.success, .text-green-600, [role="status"]');
  await expect(success).toBeVisible();
  await expect(success).toContainText(message);
}

// Test data generators
export function generateUniqueProjectName(): string {
  return `Test Project ${Date.now()}`;
}

export function generateUniqueEmail(): string {
  return `test-${Date.now()}@example.com`;
}

export { expect };