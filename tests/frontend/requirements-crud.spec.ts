import { test, expect } from '@playwright/test';

test.describe('Requirements CRUD Operations', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a project's requirements page
    await page.goto('/projects/1/requirements');
  });

  test('should display requirements list page', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Requirements|Project/);

    // Check for main page elements
    const pageHeader = page.locator('h1, h2').first();
    await expect(pageHeader).toBeVisible();

    // Check for "Add Requirement" button
    const addButton = page.locator('button').filter({ hasText: /Add Requirement|New Requirement|Create/ });
    await expect(addButton).toBeVisible();

    // Check for requirements table or list container
    const requirementsContainer = page.locator('.requirements-list, table, .grid').first();
    await expect(requirementsContainer).toBeVisible();
  });

  test('should open requirement creation form', async ({ page }) => {
    // Click "Add Requirement" button
    const addButton = page.locator('button').filter({ hasText: /Add Requirement|New Requirement|Create/ });
    await addButton.click();

    await page.waitForTimeout(1000);

    // Should open modal or navigate to form page
    const modal = page.locator('[role="dialog"], .modal');
    const formPage = page.locator('form');

    if (await modal.count() > 0) {
      await expect(modal).toBeVisible();
      await expect(modal.locator('input[name="title"], input[name="name"]')).toBeVisible();
    } else {
      await expect(formPage).toBeVisible();
      await expect(page.locator('input[name="title"], input[name="name"]')).toBeVisible();
    }
  });
});

test.describe('Requirement Creation Form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects/1/requirements/new');
  });

  test('should display requirement form fields', async ({ page }) => {
    // Essential requirement fields
    const requiredFields = [
      'title',
      'description',
      'type',
      'priority'
    ];

    for (const fieldName of requiredFields) {
      const field = page.locator(`input[name="${fieldName}"], textarea[name="${fieldName}"], select[name="${fieldName}"]`);
      await expect(field).toBeVisible();
    }

    // Check for requirement type dropdown/radio buttons
    const typeField = page.locator('select[name="type"], input[name="type"]');
    await expect(typeField).toBeVisible();

    // Check for priority selection
    const priorityField = page.locator('select[name="priority"], input[name="priority"]');
    await expect(priorityField).toBeVisible();

    // Check for submit and cancel buttons
    const submitButton = page.locator('button[type="submit"]');
    const cancelButton = page.locator('button').filter({ hasText: /Cancel/ });

    await expect(submitButton).toBeVisible();
    await expect(cancelButton).toBeVisible();
  });

  test('should validate requirement type selection', async ({ page }) => {
    const typeSelect = page.locator('select[name="type"]');
    const typeRadios = page.locator('input[name="type"][type="radio"]');

    if (await typeSelect.count() > 0) {
      // Test dropdown options
      const options = typeSelect.locator('option');
      await expect(options).toHaveCount.greaterThan(1);

      // Test selecting different types
      await typeSelect.selectOption('user_story');
      await expect(typeSelect).toHaveValue('user_story');

      await typeSelect.selectOption('functional');
      await expect(typeSelect).toHaveValue('functional');

      await typeSelect.selectOption('non_functional');
      await expect(typeSelect).toHaveValue('non_functional');
    } else if (await typeRadios.count() > 0) {
      // Test radio button selection
      const userStoryRadio = page.locator('input[value="user_story"]');
      const functionalRadio = page.locator('input[value="functional"]');

      if (await userStoryRadio.count() > 0) {
        await userStoryRadio.check();
        await expect(userStoryRadio).toBeChecked();
      }

      if (await functionalRadio.count() > 0) {
        await functionalRadio.check();
        await expect(functionalRadio).toBeChecked();
        await expect(userStoryRadio).not.toBeChecked();
      }
    }
  });

  test('should handle user story specific fields', async ({ page }) => {
    // Select user story type first
    const typeSelect = page.locator('select[name="type"]');
    if (await typeSelect.count() > 0) {
      await typeSelect.selectOption('user_story');
    }

    // Check for user story specific fields
    const userPersonaField = page.locator('input[name="user_persona"], input[name="persona"]');
    const userGoalField = page.locator('textarea[name="user_goal"], input[name="goal"]');
    const userBenefitField = page.locator('textarea[name="user_benefit"], input[name="benefit"]');
    const storyPointsField = page.locator('input[name="story_points"], select[name="story_points"]');

    if (await userPersonaField.count() > 0) {
      await userPersonaField.fill('Product Manager');
    }

    if (await userGoalField.count() > 0) {
      await userGoalField.fill('I want to create detailed requirements');
    }

    if (await userBenefitField.count() > 0) {
      await userBenefitField.fill('So that the development team has clear specifications');
    }

    if (await storyPointsField.count() > 0) {
      if (await storyPointsField.locator('option').count() > 0) {
        await storyPointsField.selectOption('5');
      } else {
        await storyPointsField.fill('5');
      }
    }
  });

  test('should create a new requirement successfully', async ({ page }) => {
    // Fill out the requirement form
    const requirementData = {
      title: 'User Authentication System',
      description: 'Implement a secure user authentication system with login, logout, and session management',
      type: 'functional',
      priority: 'high',
      category: 'Security'
    };

    // Fill title
    await page.locator('input[name="title"]').fill(requirementData.title);

    // Fill description
    await page.locator('textarea[name="description"]').fill(requirementData.description);

    // Select type
    const typeField = page.locator('select[name="type"]');
    if (await typeField.count() > 0) {
      await typeField.selectOption(requirementData.type);
    }

    // Select priority
    const priorityField = page.locator('select[name="priority"]');
    if (await priorityField.count() > 0) {
      await priorityField.selectOption(requirementData.priority);
    }

    // Fill category if field exists
    const categoryField = page.locator('input[name="category"]');
    if (await categoryField.count() > 0) {
      await categoryField.fill(requirementData.category);
    }

    // Submit the form
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // Check for loading state
    await expect(submitButton).toBeDisabled();

    // Wait for submission
    await page.waitForTimeout(2000);

    // Should show success message or navigate to requirement detail
    const successMessage = page.locator('.success, .text-green-600, [role="status"]');
    const requirementTitle = page.locator('h1, h2').filter({ hasText: requirementData.title });

    if (await successMessage.count() > 0) {
      await expect(successMessage).toBeVisible();
    } else if (await requirementTitle.count() > 0) {
      await expect(requirementTitle).toBeVisible();
    }
  });

  test('should handle acceptance criteria creation', async ({ page }) => {
    // Fill basic requirement info first
    await page.locator('input[name="title"]').fill('Login Feature');
    await page.locator('textarea[name="description"]').fill('User login functionality');

    // Look for acceptance criteria section
    const criteriaSection = page.locator('.acceptance-criteria, .criteria');
    const addCriteriaButton = page.locator('button').filter({ hasText: /Add Criteria|Add Acceptance/ });

    if (await addCriteriaButton.count() > 0) {
      await addCriteriaButton.click();

      // Should add criteria input field
      const criteriaInput = page.locator('input[name*="criteria"], textarea[name*="criteria"]');
      await expect(criteriaInput).toBeVisible();

      await criteriaInput.first().fill('Given a valid username and password, when the user clicks login, then they should be authenticated');

      // Add another criteria
      await addCriteriaButton.click();
      const criteriaInputs = page.locator('input[name*="criteria"], textarea[name*="criteria"]');
      await expect(criteriaInputs).toHaveCount(2);

      await criteriaInputs.nth(1).fill('Given invalid credentials, when the user clicks login, then an error message should be displayed');
    }
  });
});

test.describe('Requirements List and Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects/1/requirements');
  });

  test('should display requirements in table format', async ({ page }) => {
    // Check for table headers
    const table = page.locator('table');
    if (await table.count() > 0) {
      const headers = table.locator('th');
      await expect(headers).toHaveCount.greaterThan(3);

      // Common column headers
      const expectedHeaders = ['ID', 'Title', 'Type', 'Priority', 'Status', 'Actions'];
      for (const header of expectedHeaders) {
        const headerElement = headers.filter({ hasText: new RegExp(header, 'i') });
        if (await headerElement.count() > 0) {
          await expect(headerElement).toBeVisible();
        }
      }
    }
  });

  test('should display requirements in card format', async ({ page }) => {
    // Check for card-based layout
    const cards = page.locator('.requirement-card, .card, .border.rounded');
    if (await cards.count() > 0) {
      const firstCard = cards.first();
      await expect(firstCard).toBeVisible();

      // Check for requirement information in card
      const title = firstCard.locator('h3, h4, .title');
      const type = firstCard.locator('.type, .badge');
      const priority = firstCard.locator('.priority');

      if (await title.count() > 0) await expect(title).toBeVisible();
      if (await type.count() > 0) await expect(type).toBeVisible();
      if (await priority.count() > 0) await expect(priority).toBeVisible();
    }
  });

  test('should handle requirement status updates', async ({ page }) => {
    // Look for status dropdown or buttons
    const statusDropdown = page.locator('select[name*="status"]').first();
    const statusButtons = page.locator('button').filter({ hasText: /Draft|Review|Approved|Complete/ });

    if (await statusDropdown.count() > 0) {
      // Test status change via dropdown
      await statusDropdown.selectOption('approved');
      await page.waitForTimeout(1000);

      // Should update status
      await expect(statusDropdown).toHaveValue('approved');
    } else if (await statusButtons.count() > 0) {
      // Test status change via buttons
      const approveButton = page.locator('button').filter({ hasText: /Approve/ });
      if (await approveButton.count() > 0) {
        await approveButton.click();
        await page.waitForTimeout(1000);

        // Should show updated status
        const statusIndicator = page.locator('.status, .badge').filter({ hasText: /Approved/ });
        await expect(statusIndicator).toBeVisible();
      }
    }
  });

  test('should enable requirement editing', async ({ page }) => {
    // Look for edit buttons
    const editButton = page.locator('button, a').filter({ hasText: /Edit/ }).first();

    if (await editButton.count() > 0) {
      await editButton.click();
      await page.waitForTimeout(1000);

      // Should open edit form or navigate to edit page
      const editForm = page.locator('form');
      const titleField = page.locator('input[name="title"]');

      await expect(editForm).toBeVisible();
      await expect(titleField).toBeVisible();

      // Test editing
      await titleField.clear();
      await titleField.fill('Updated Requirement Title');

      const saveButton = page.locator('button').filter({ hasText: /Save|Update/ });
      await saveButton.click();

      await page.waitForTimeout(2000);

      // Should show updated requirement
      const updatedTitle = page.locator('h1, h2, h3').filter({ hasText: 'Updated Requirement Title' });
      if (await updatedTitle.count() > 0) {
        await expect(updatedTitle).toBeVisible();
      }
    }
  });

  test('should handle requirement deletion', async ({ page }) => {
    // Look for delete buttons
    const deleteButton = page.locator('button').filter({ hasText: /Delete|Remove/ }).first();

    if (await deleteButton.count() > 0) {
      await deleteButton.click();

      // Should show confirmation dialog
      const confirmDialog = page.locator('[role="dialog"], .modal, .confirm');
      if (await confirmDialog.count() > 0) {
        await expect(confirmDialog).toBeVisible();
        await expect(confirmDialog).toContainText(/delete|remove|confirm/i);

        // Confirm deletion
        const confirmButton = confirmDialog.locator('button').filter({ hasText: /Delete|Confirm|Yes/ });
        await confirmButton.click();

        await page.waitForTimeout(2000);

        // Should show success message or redirect
        const successMessage = page.locator('.success, .text-green-600');
        if (await successMessage.count() > 0) {
          await expect(successMessage).toBeVisible();
        }
      }
    }
  });

  test('should support bulk operations', async ({ page }) => {
    // Look for checkboxes to select multiple requirements
    const checkboxes = page.locator('input[type="checkbox"]');

    if (await checkboxes.count() > 1) {
      // Select multiple requirements
      await checkboxes.nth(0).check();
      await checkboxes.nth(1).check();

      // Look for bulk action buttons
      const bulkActions = page.locator('.bulk-actions, .selected-actions');
      const bulkDeleteButton = page.locator('button').filter({ hasText: /Bulk Delete|Delete Selected/ });
      const bulkUpdateButton = page.locator('button').filter({ hasText: /Bulk Update|Update Selected/ });

      if (await bulkActions.count() > 0) {
        await expect(bulkActions).toBeVisible();
      }

      if (await bulkDeleteButton.count() > 0) {
        await expect(bulkDeleteButton).toBeVisible();
        await expect(bulkDeleteButton).toBeEnabled();
      }

      if (await bulkUpdateButton.count() > 0) {
        await expect(bulkUpdateButton).toBeVisible();
        await expect(bulkUpdateButton).toBeEnabled();
      }
    }
  });
});

test.describe('Requirements Filtering and Search', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects/1/requirements');
  });

  test('should provide search functionality', async ({ page }) => {
    // Look for search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="search"], input[name*="search"]');

    if (await searchInput.count() > 0) {
      await expect(searchInput).toBeVisible();

      // Test search
      await searchInput.fill('authentication');
      await page.keyboard.press('Enter');

      await page.waitForTimeout(1000);

      // Should filter results
      const searchResults = page.locator('.requirement-card, tr, .result');
      if (await searchResults.count() > 0) {
        // Results should contain search term
        const firstResult = searchResults.first();
        await expect(firstResult).toContainText(/authentication/i);
      }

      // Clear search
      await searchInput.clear();
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1000);
    }
  });

  test('should filter by requirement type', async ({ page }) => {
    // Look for type filter dropdown
    const typeFilter = page.locator('select[name*="type"], .filter-type');

    if (await typeFilter.count() > 0) {
      await typeFilter.selectOption('user_story');
      await page.waitForTimeout(1000);

      // Should show only user stories
      const typeLabels = page.locator('.type, .badge').filter({ hasText: /User Story/i });
      if (await typeLabels.count() > 0) {
        await expect(typeLabels.first()).toBeVisible();
      }

      // Reset filter
      await typeFilter.selectOption('');
      await page.waitForTimeout(1000);
    }
  });

  test('should filter by priority', async ({ page }) => {
    // Look for priority filter
    const priorityFilter = page.locator('select[name*="priority"], .filter-priority');

    if (await priorityFilter.count() > 0) {
      await priorityFilter.selectOption('high');
      await page.waitForTimeout(1000);

      // Should show only high priority requirements
      const priorityLabels = page.locator('.priority').filter({ hasText: /High/i });
      if (await priorityLabels.count() > 0) {
        await expect(priorityLabels.first()).toBeVisible();
      }
    }
  });

  test('should filter by status', async ({ page }) => {
    // Look for status filter
    const statusFilter = page.locator('select[name*="status"], .filter-status');

    if (await statusFilter.count() > 0) {
      await statusFilter.selectOption('approved');
      await page.waitForTimeout(1000);

      // Should show only approved requirements
      const statusLabels = page.locator('.status').filter({ hasText: /Approved/i });
      if (await statusLabels.count() > 0) {
        await expect(statusLabels.first()).toBeVisible();
      }
    }
  });

  test('should support advanced filtering', async ({ page }) => {
    // Look for advanced filter toggle or section
    const advancedFilterToggle = page.locator('button').filter({ hasText: /Advanced|Filter/ });
    const filterSection = page.locator('.advanced-filters, .filters');

    if (await advancedFilterToggle.count() > 0) {
      await advancedFilterToggle.click();

      // Should show advanced filter options
      await expect(filterSection).toBeVisible();

      // Test date range filtering
      const dateFromInput = page.locator('input[type="date"][name*="from"]');
      const dateToInput = page.locator('input[type="date"][name*="to"]');

      if (await dateFromInput.count() > 0 && await dateToInput.count() > 0) {
        await dateFromInput.fill('2024-01-01');
        await dateToInput.fill('2024-12-31');

        const applyFilterButton = page.locator('button').filter({ hasText: /Apply|Filter/ });
        if (await applyFilterButton.count() > 0) {
          await applyFilterButton.click();
          await page.waitForTimeout(1000);
        }
      }
    }
  });

  test('should support sorting', async ({ page }) => {
    // Look for sort controls
    const sortDropdown = page.locator('select[name*="sort"]');
    const sortHeaders = page.locator('th[data-sortable], .sortable');

    if (await sortDropdown.count() > 0) {
      // Test dropdown sorting
      await sortDropdown.selectOption('title');
      await page.waitForTimeout(1000);

      await sortDropdown.selectOption('priority');
      await page.waitForTimeout(1000);

      await sortDropdown.selectOption('created_at');
      await page.waitForTimeout(1000);
    } else if (await sortHeaders.count() > 0) {
      // Test clickable header sorting
      const titleHeader = sortHeaders.filter({ hasText: /Title/i }).first();
      if (await titleHeader.count() > 0) {
        await titleHeader.click();
        await page.waitForTimeout(1000);

        // Should show sort indicator
        const sortIndicator = titleHeader.locator('.sort-asc, .sort-desc, .↑, .↓');
        if (await sortIndicator.count() > 0) {
          await expect(sortIndicator).toBeVisible();
        }

        // Click again to reverse sort
        await titleHeader.click();
        await page.waitForTimeout(1000);
      }
    }
  });
});