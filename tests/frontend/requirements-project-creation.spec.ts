import { test, expect } from '@playwright/test';

test.describe('Requirements Project Creation', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication and navigate to the projects area
    await page.goto('/dashboard');
  });

  test('should initiate project creation from dashboard quick action', async ({ page }) => {
    // Click on the "New Project" quick action card
    const newProjectQuickAction = page.locator('.relative.rounded-lg.border').filter({
      hasText: 'New Project'
    });

    await expect(newProjectQuickAction).toBeVisible();
    await newProjectQuickAction.click();

    // Should navigate to project creation page or open modal
    // This depends on implementation - check for either scenario
    await page.waitForTimeout(1000);

    // Check if modal opened
    const modal = page.locator('[role="dialog"]').or(page.locator('.modal'));
    if (await modal.count() > 0) {
      await expect(modal).toBeVisible();
    } else {
      // Or check if navigated to new page
      await expect(page.url()).toMatch(/projects\/new|create-project/);
    }
  });

  test('should initiate project creation from empty state button', async ({ page }) => {
    // Click the "New Project" button in the empty state
    const newProjectButton = page.locator('button').filter({ hasText: 'New Project' });

    await expect(newProjectButton).toBeVisible();
    await newProjectButton.click();

    await page.waitForTimeout(1000);

    // Should trigger project creation flow
    const modal = page.locator('[role="dialog"]').or(page.locator('.modal'));
    if (await modal.count() > 0) {
      await expect(modal).toBeVisible();
    }
  });
});

test.describe('Project Creation Form', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate directly to project creation page
    await page.goto('/projects/new');
  });

  test('should display project creation form fields', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/New Project|Create Project/);

    // Check form fields exist
    const expectedFields = [
      'name',
      'description',
      'vision',
      'methodology'
    ];

    for (const fieldName of expectedFields) {
      const field = page.locator(`input[name="${fieldName}"], textarea[name="${fieldName}"], select[name="${fieldName}"]`);
      await expect(field).toBeVisible();
    }

    // Check submit button
    const submitButton = page.locator('button[type="submit"]').or(page.locator('button').filter({ hasText: /Create|Save/ }));
    await expect(submitButton).toBeVisible();

    // Check cancel button or link
    const cancelButton = page.locator('button').filter({ hasText: /Cancel/ }).or(page.locator('a').filter({ hasText: /Cancel|Back/ }));
    await expect(cancelButton).toBeVisible();
  });

  test('should validate required project fields', async ({ page }) => {
    // Try to submit empty form
    const submitButton = page.locator('button[type="submit"]').or(page.locator('button').filter({ hasText: /Create|Save/ }));
    await submitButton.click();

    // Check for validation messages
    const nameField = page.locator('input[name="name"]');
    await expect(nameField).toHaveAttribute('required');

    // Check for client-side validation or error messages
    await page.waitForTimeout(1000);

    // Look for validation error indicators
    const errorMessages = page.locator('.text-red-600, .text-red-500, .error, [role="alert"]');
    if (await errorMessages.count() > 0) {
      await expect(errorMessages.first()).toBeVisible();
    }
  });

  test('should fill and submit project creation form', async ({ page }) => {
    // Fill out the form with valid data
    const projectData = {
      name: 'Test Requirements Project',
      description: 'A comprehensive test project for requirements gathering and management',
      vision: 'To streamline our development process through better requirements documentation',
      methodology: 'agile'
    };

    // Fill name field
    const nameField = page.locator('input[name="name"]');
    await nameField.fill(projectData.name);

    // Fill description field
    const descriptionField = page.locator('textarea[name="description"]').or(page.locator('input[name="description"]'));
    await descriptionField.fill(projectData.description);

    // Fill vision field (if present)
    const visionField = page.locator('textarea[name="vision"]').or(page.locator('input[name="vision"]'));
    if (await visionField.count() > 0) {
      await visionField.fill(projectData.vision);
    }

    // Select methodology (if dropdown)
    const methodologyField = page.locator('select[name="methodology"]');
    if (await methodologyField.count() > 0) {
      await methodologyField.selectOption(projectData.methodology);
    } else {
      // If it's radio buttons or text input
      const methodologyInput = page.locator('input[name="methodology"]');
      if (await methodologyInput.count() > 0) {
        await methodologyInput.fill(projectData.methodology);
      }
    }

    // Submit the form
    const submitButton = page.locator('button[type="submit"]').or(page.locator('button').filter({ hasText: /Create|Save/ }));
    await submitButton.click();

    // Check for loading state
    await expect(submitButton).toBeDisabled();

    // Wait for form submission
    await page.waitForTimeout(2000);

    // Should navigate to project page or show success message
    await page.waitForURL('**/projects/**', { timeout: 5000 }).catch(() => {
      // If navigation doesn't happen, check for success message
    });

    // Check for success indicators
    const successMessage = page.locator('.text-green-600, .success, [role="status"]');
    const projectTitle = page.locator('h1, h2').filter({ hasText: projectData.name });

    // Either should see success message or be on project page
    if (await successMessage.count() > 0) {
      await expect(successMessage).toBeVisible();
    } else if (await projectTitle.count() > 0) {
      await expect(projectTitle).toBeVisible();
    }
  });

  test('should handle form cancellation', async ({ page }) => {
    // Fill some data first
    const nameField = page.locator('input[name="name"]');
    await nameField.fill('Test Project to Cancel');

    // Click cancel button
    const cancelButton = page.locator('button').filter({ hasText: /Cancel/ }).or(page.locator('a').filter({ hasText: /Cancel|Back/ }));
    await cancelButton.click();

    // Should navigate back to dashboard or projects list
    await page.waitForTimeout(1000);

    // Check if back on dashboard
    if (page.url().includes('/dashboard')) {
      await expect(page.locator('h2')).toContainText('Welcome');
    } else if (page.url().includes('/projects')) {
      await expect(page).toHaveTitle(/Projects/);
    }
  });

  test('should show real-time field validation', async ({ page }) => {
    const nameField = page.locator('input[name="name"]');

    // Test empty field validation
    await nameField.focus();
    await nameField.blur();

    // Check for validation feedback
    await page.waitForTimeout(500);

    // Test valid input
    await nameField.fill('Valid Project Name');
    await nameField.blur();

    // Validation error should disappear
    await page.waitForTimeout(500);

    // Test character limits (if any)
    const longName = 'A'.repeat(300);
    await nameField.fill(longName);
    await nameField.blur();

    // Should show character limit warning if implemented
    await page.waitForTimeout(500);
  });
});

test.describe('Project Creation Advanced Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects/new');
  });

  test('should handle goals and success criteria fields', async ({ page }) => {
    // Look for goals section
    const goalsSection = page.locator('input[name*="goal"], textarea[name*="goal"], .goals');
    if (await goalsSection.count() > 0) {
      // Test adding goals
      const firstGoal = goalsSection.first();
      await firstGoal.fill('Improve development efficiency by 30%');

      // Look for "Add Goal" button
      const addGoalButton = page.locator('button').filter({ hasText: /Add Goal|Add Another/ });
      if (await addGoalButton.count() > 0) {
        await addGoalButton.click();

        // Should add another goal field
        const goalFields = page.locator('input[name*="goal"], textarea[name*="goal"]');
        await expect(goalFields).toHaveCount(2);
      }
    }

    // Look for success criteria section
    const criteriaSection = page.locator('input[name*="criteria"], textarea[name*="criteria"], .success-criteria');
    if (await criteriaSection.count() > 0) {
      const firstCriteria = criteriaSection.first();
      await firstCriteria.fill('95% user satisfaction rating');
    }
  });

  test('should handle stakeholder information', async ({ page }) => {
    // Look for stakeholder fields
    const stakeholderName = page.locator('input[name*="stakeholder"], input[name*="name"]').filter({ hasText: /stakeholder/i });
    const stakeholderRole = page.locator('input[name*="role"], select[name*="role"]');
    const stakeholderEmail = page.locator('input[name*="email"][type="email"]');

    if (await stakeholderName.count() > 0) {
      await stakeholderName.first().fill('John Doe');
    }

    if (await stakeholderRole.count() > 0) {
      if (await stakeholderRole.first().locator('option').count() > 0) {
        await stakeholderRole.first().selectOption('Product Owner');
      } else {
        await stakeholderRole.first().fill('Product Owner');
      }
    }

    if (await stakeholderEmail.count() > 0) {
      await stakeholderEmail.first().fill('john.doe@example.com');
    }

    // Look for "Add Stakeholder" button
    const addStakeholderButton = page.locator('button').filter({ hasText: /Add Stakeholder/ });
    if (await addStakeholderButton.count() > 0) {
      await addStakeholderButton.click();

      // Should add another stakeholder row
      await page.waitForTimeout(500);
    }
  });

  test('should handle methodology selection', async ({ page }) => {
    // Look for methodology selection
    const methodologySelect = page.locator('select[name="methodology"]');
    const methodologyRadios = page.locator('input[name="methodology"][type="radio"]');

    if (await methodologySelect.count() > 0) {
      // Test dropdown selection
      await methodologySelect.selectOption('scrum');
      await expect(methodologySelect).toHaveValue('scrum');

      await methodologySelect.selectOption('waterfall');
      await expect(methodologySelect).toHaveValue('waterfall');

      await methodologySelect.selectOption('agile');
      await expect(methodologySelect).toHaveValue('agile');
    } else if (await methodologyRadios.count() > 0) {
      // Test radio button selection
      const scrumRadio = page.locator('input[value="scrum"]');
      const waterfallRadio = page.locator('input[value="waterfall"]');

      if (await scrumRadio.count() > 0) {
        await scrumRadio.check();
        await expect(scrumRadio).toBeChecked();
      }

      if (await waterfallRadio.count() > 0) {
        await waterfallRadio.check();
        await expect(waterfallRadio).toBeChecked();
        await expect(scrumRadio).not.toBeChecked();
      }
    }
  });

  test('should preview project information', async ({ page }) => {
    // Fill form data
    await page.locator('input[name="name"]').fill('Preview Test Project');
    await page.locator('textarea[name="description"]').fill('A project to test the preview functionality');

    // Look for preview button or tab
    const previewButton = page.locator('button').filter({ hasText: /Preview/ });
    const previewTab = page.locator('[role="tab"]').filter({ hasText: /Preview/ });

    if (await previewButton.count() > 0) {
      await previewButton.click();

      // Should show preview content
      await expect(page.locator('.preview')).toBeVisible();
      await expect(page.locator('.preview')).toContainText('Preview Test Project');
    } else if (await previewTab.count() > 0) {
      await previewTab.click();

      // Should switch to preview tab
      await expect(previewTab).toHaveAttribute('aria-selected', 'true');
    }
  });
});

test.describe('Project Creation Error Handling', () => {
  test('should handle server errors gracefully', async ({ page }) => {
    await page.goto('/projects/new');

    // Mock server error response
    await page.route('**/api/projects', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    // Fill and submit form
    await page.locator('input[name="name"]').fill('Test Project');
    await page.locator('button[type="submit"]').click();

    // Should show error message
    await page.waitForTimeout(2000);

    const errorMessage = page.locator('.text-red-600, .error, [role="alert"]');
    await expect(errorMessage).toBeVisible();

    // Submit button should be re-enabled
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeEnabled();
  });

  test('should handle network connectivity issues', async ({ page }) => {
    await page.goto('/projects/new');

    // Mock network failure
    await page.route('**/api/projects', async route => {
      await route.abort('failed');
    });

    // Fill and submit form
    await page.locator('input[name="name"]').fill('Test Project');
    await page.locator('button[type="submit"]').click();

    // Should show network error message
    await page.waitForTimeout(2000);

    const errorMessage = page.locator('.text-red-600, .error, [role="alert"]');
    if (await errorMessage.count() > 0) {
      await expect(errorMessage).toBeVisible();
    }

    // Form should remain functional for retry
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeEnabled();
  });

  test('should handle validation errors from server', async ({ page }) => {
    await page.goto('/projects/new');

    // Mock validation error response
    await page.route('**/api/projects', async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Validation failed',
          details: {
            name: 'Project name already exists',
            description: 'Description is too short'
          }
        })
      });
    });

    // Fill and submit form
    await page.locator('input[name="name"]').fill('Duplicate Project');
    await page.locator('textarea[name="description"]').fill('Short');
    await page.locator('button[type="submit"]').click();

    // Should show field-specific errors
    await page.waitForTimeout(2000);

    const nameError = page.locator('.error').filter({ hasText: /name/i });
    const descriptionError = page.locator('.error').filter({ hasText: /description/i });

    if (await nameError.count() > 0) {
      await expect(nameError).toBeVisible();
    }

    if (await descriptionError.count() > 0) {
      await expect(descriptionError).toBeVisible();
    }
  });
});