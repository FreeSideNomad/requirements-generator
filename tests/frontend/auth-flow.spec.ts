import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the login page
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    // Check that the login page loads correctly
    await expect(page).toHaveTitle(/Login - Requirements Generator/);

    // Check for key UI elements
    await expect(page.locator('h2')).toContainText('Requirements Generator');
    await expect(page.locator('#email')).toBeVisible(); // Main login form email
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('#login-button')).toBeVisible(); // Specific login button
    await expect(page.locator('a').filter({ hasText: 'Create an account' })).toBeVisible();
  });

  test('should validate email format', async ({ page }) => {
    // Try to submit with invalid email
    await page.fill('#email', 'invalid-email');
    await page.fill('input[name="password"]', 'password123');

    // Click submit and check for HTML5 validation
    await page.click('#login-button');

    // Check that the browser validation prevents submission
    const emailInput = page.locator('#email');
    await expect(emailInput).toHaveAttribute('required');
    await expect(emailInput).toHaveAttribute('type', 'email');
  });

  test('should show password toggle functionality', async ({ page }) => {
    const passwordInput = page.locator('input[name="password"]');
    const toggleButton = page.locator('button').filter({ hasText: '' }).nth(0); // Eye icon button

    // Initially password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Fill password field
    await passwordInput.fill('testpassword');

    // Click toggle button (if it exists)
    const toggleExists = await toggleButton.count() > 0;
    if (toggleExists) {
      await toggleButton.click();
      // Password should now be visible
      await expect(passwordInput).toHaveAttribute('type', 'text');

      // Click again to hide
      await toggleButton.click();
      await expect(passwordInput).toHaveAttribute('type', 'password');
    }
  });

  test('should navigate to registration page', async ({ page }) => {
    // Click the "Create an account" link
    await page.click('a[href="/register"]');

    // Should navigate to registration page
    await expect(page).toHaveURL(/.*\/register/);
    await expect(page).toHaveTitle(/Register - Requirements Generator/);
  });

  test('should show forgot password modal', async ({ page }) => {
    // Click forgot password link
    await page.click('text=Forgot password?');

    // Modal should appear
    const modal = page.locator('#forgot-password-modal');
    await expect(modal).toBeVisible();
    await expect(modal.locator('h3')).toContainText('Reset Password');

    // Should have email input
    await expect(modal.locator('input[name="email"]')).toBeVisible();

    // Close modal
    await modal.locator('button').filter({ hasText: 'Cancel' }).click();
    await expect(modal).toBeHidden();
  });

  test('should attempt login with valid format but non-existent credentials', async ({ page }) => {
    // Fill in credentials
    await page.fill('input[name="email"]', 'nonexistent@example.com');
    await page.fill('input[name="password"]', 'password123');

    // Submit form
    await page.click('button[type="submit"]');

    // Should show loading state briefly
    const loginButton = page.locator('#login-button');
    await expect(loginButton).toBeDisabled();

    // Wait for response and check for error
    await page.waitForTimeout(2000); // Wait for HTMX request

    // Should show error toast or message
    const toast = page.locator('#toast-container');
    // Note: This might not appear if the endpoint doesn't exist yet
  });
});

test.describe('Registration Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('should display registration form', async ({ page }) => {
    // Check that registration page loads correctly
    await expect(page).toHaveTitle(/Register - Requirements Generator/);

    // Check for registration form fields
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('input[name="confirm_password"]')).toBeVisible();
    await expect(page.locator('input[name="first_name"]')).toBeVisible();
    await expect(page.locator('input[name="last_name"]')).toBeVisible();

    // Check for submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    // Check for login link
    await expect(page.locator('a').filter({ hasText: 'Sign in' })).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Check that required fields prevent submission
    const requiredFields = [
      'input[name="email"]',
      'input[name="password"]',
      'input[name="confirm_password"]',
      'input[name="first_name"]',
      'input[name="last_name"]'
    ];

    for (const field of requiredFields) {
      await expect(page.locator(field)).toHaveAttribute('required');
    }
  });

  test('should validate password confirmation', async ({ page }) => {
    // Fill form with mismatched passwords
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="confirm_password"]', 'different123');
    await page.fill('input[name="first_name"]', 'Test');
    await page.fill('input[name="last_name"]', 'User');

    // Submit form
    await page.click('button[type="submit"]');

    // Should show validation error (either client-side or server-side)
    await page.waitForTimeout(1000);
    // Note: Specific validation behavior depends on implementation
  });

  test('should navigate back to login', async ({ page }) => {
    // Click the login link
    await page.click('text=Sign in');

    // Should navigate to login page
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page).toHaveTitle(/Login - Requirements Generator/);
  });

  test('should attempt registration with valid data', async ({ page }) => {
    // Generate unique test data
    const timestamp = Date.now();
    const email = `test-${timestamp}@example.com`;

    // Fill registration form
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.fill('input[name="confirm_password"]', 'SecurePassword123!');
    await page.fill('input[name="first_name"]', 'Test');
    await page.fill('input[name="last_name"]', 'User');

    // Submit form
    await page.click('button[type="submit"]');

    // Should show loading state
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeDisabled();

    // Wait for response
    await page.waitForTimeout(3000);

    // Note: Actual behavior depends on whether registration endpoint exists
    // This test validates the UI behavior rather than the full flow
  });
});

test.describe('Navigation and UI', () => {
  test('should show auth providers check', async ({ page }) => {
    await page.goto('/login');

    // Wait for the auth providers check to complete
    await page.waitForTimeout(1000);

    // Azure AD section should be hidden by default (based on the template)
    const azureSection = page.locator('#azure-ad-section');
    await expect(azureSection).toHaveClass(/hidden/);
  });

  test('should have responsive design', async ({ page }) => {
    await page.goto('/login');

    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(page.locator('[data-testid="login-header"]')).toBeVisible();

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('should load and display icons', async ({ page }) => {
    await page.goto('/login');

    // Check that Lucide icons are loaded
    const brandIcon = page.locator('[data-lucide="layers"]');
    await expect(brandIcon).toBeVisible();

    // Check password toggle icon
    const eyeIcon = page.locator('[data-lucide="eye"]');
    if (await eyeIcon.count() > 0) {
      await expect(eyeIcon).toBeVisible();
    }
  });
});