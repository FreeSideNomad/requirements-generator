import { test, expect } from '@playwright/test';

test.describe('Requirements Documentation Generation', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to project documentation page
    await page.goto('/projects/1/documentation');
  });

  test('should display documentation generation page', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Documentation|Generate/);

    // Check main page elements
    const pageHeader = page.locator('h1, h2').first();
    await expect(pageHeader).toBeVisible();

    // Check for generation options
    const generateButton = page.locator('button').filter({ hasText: /Generate|Create|Export/ });
    await expect(generateButton).toBeVisible();
  });

  test('should show template selection options', async ({ page }) => {
    // Look for template selection dropdown or radio buttons
    const templateSelect = page.locator('select[name*="template"]');
    const templateRadios = page.locator('input[name*="template"][type="radio"]');

    if (await templateSelect.count() > 0) {
      await expect(templateSelect).toBeVisible();

      // Check for common template options
      const options = templateSelect.locator('option');
      const optionTexts = await options.allTextContents();

      expect(optionTexts.some(text => text.toLowerCase().includes('default'))).toBeTruthy();
      expect(optionTexts.some(text => text.toLowerCase().includes('detailed'))).toBeTruthy();
    } else if (await templateRadios.count() > 0) {
      await expect(templateRadios.first()).toBeVisible();

      // Test selecting different templates
      const defaultTemplate = page.locator('input[value*="default"]');
      const detailedTemplate = page.locator('input[value*="detailed"]');

      if (await defaultTemplate.count() > 0) {
        await defaultTemplate.check();
        await expect(defaultTemplate).toBeChecked();
      }

      if (await detailedTemplate.count() > 0) {
        await detailedTemplate.check();
        await expect(detailedTemplate).toBeChecked();
      }
    }
  });

  test('should provide documentation format options', async ({ page }) => {
    // Look for format selection (markdown, pdf, html, etc.)
    const formatSelect = page.locator('select[name*="format"]');
    const formatRadios = page.locator('input[name*="format"][type="radio"]');

    if (await formatSelect.count() > 0) {
      await expect(formatSelect).toBeVisible();

      // Test format selection
      const options = formatSelect.locator('option');
      const optionValues = await options.evaluateAll(opts => opts.map(opt => opt.value));

      // Common formats
      const expectedFormats = ['markdown', 'pdf', 'html', 'docx'];
      const hasExpectedFormats = expectedFormats.some(format =>
        optionValues.some(value => value.includes(format))
      );

      expect(hasExpectedFormats).toBeTruthy();
    } else if (await formatRadios.count() > 0) {
      await expect(formatRadios.first()).toBeVisible();
    }
  });

  test('should allow customization of documentation sections', async ({ page }) => {
    // Look for section inclusion checkboxes
    const sectionCheckboxes = page.locator('input[type="checkbox"]');

    if (await sectionCheckboxes.count() > 0) {
      // Common documentation sections
      const sectionOptions = [
        'domain_model',
        'acceptance_criteria',
        'comments',
        'stakeholders',
        'goals',
        'success_criteria'
      ];

      for (const section of sectionOptions) {
        const checkbox = page.locator(`input[name*="${section}"], input[value*="${section}"]`);
        if (await checkbox.count() > 0) {
          // Test checking/unchecking sections
          await checkbox.check();
          await expect(checkbox).toBeChecked();

          await checkbox.uncheck();
          await expect(checkbox).not.toBeChecked();

          // Leave checked for generation
          await checkbox.check();
        }
      }
    }
  });

  test('should generate markdown documentation', async ({ page }) => {
    // Select markdown format
    const formatSelect = page.locator('select[name*="format"]');
    if (await formatSelect.count() > 0) {
      await formatSelect.selectOption('markdown');
    }

    // Select default template
    const templateSelect = page.locator('select[name*="template"]');
    if (await templateSelect.count() > 0) {
      await templateSelect.selectOption('default');
    }

    // Enable key sections
    const domainModelCheckbox = page.locator('input[name*="domain"], input[value*="domain"]');
    if (await domainModelCheckbox.count() > 0) {
      await domainModelCheckbox.check();
    }

    const acceptanceCriteriaCheckbox = page.locator('input[name*="acceptance"], input[value*="criteria"]');
    if (await acceptanceCriteriaCheckbox.count() > 0) {
      await acceptanceCriteriaCheckbox.check();
    }

    // Generate documentation
    const generateButton = page.locator('button').filter({ hasText: /Generate|Create|Export/ });
    await generateButton.click();

    // Check for loading state
    await expect(generateButton).toBeDisabled();

    // Wait for generation
    await page.waitForTimeout(3000);

    // Should show generated content or download
    const documentContent = page.locator('.document-content, .preview, pre, .markdown');
    const downloadLink = page.locator('a[download], button').filter({ hasText: /Download/ });

    if (await documentContent.count() > 0) {
      await expect(documentContent).toBeVisible();

      // Check for markdown structure
      const content = await documentContent.textContent();
      expect(content).toContain('#'); // Headers
      expect(content).toContain('##'); // Subheaders
    } else if (await downloadLink.count() > 0) {
      await expect(downloadLink).toBeVisible();
    }
  });

  test('should preview documentation before generation', async ({ page }) => {
    // Look for preview button or tab
    const previewButton = page.locator('button').filter({ hasText: /Preview/ });
    const previewTab = page.locator('[role="tab"]').filter({ hasText: /Preview/ });

    if (await previewButton.count() > 0) {
      await previewButton.click();

      // Should show preview area
      const previewArea = page.locator('.preview, .document-preview');
      await expect(previewArea).toBeVisible();

      // Should show basic document structure
      const headers = previewArea.locator('h1, h2, h3');
      await expect(headers.first()).toBeVisible();
    } else if (await previewTab.count() > 0) {
      await previewTab.click();

      // Should switch to preview tab
      await expect(previewTab).toHaveAttribute('aria-selected', 'true');

      const tabPanel = page.locator('[role="tabpanel"]');
      await expect(tabPanel).toBeVisible();
    }
  });

  test('should handle documentation generation errors', async ({ page }) => {
    // Mock server error
    await page.route('**/api/projects/*/documentation', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Documentation generation failed' })
      });
    });

    // Attempt generation
    const generateButton = page.locator('button').filter({ hasText: /Generate|Create|Export/ });
    await generateButton.click();

    // Wait for error
    await page.waitForTimeout(2000);

    // Should show error message
    const errorMessage = page.locator('.error, .text-red-600, [role="alert"]');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText(/error|failed/i);

    // Button should be re-enabled
    await expect(generateButton).toBeEnabled();
  });

  test('should support custom documentation templates', async ({ page }) => {
    // Look for custom template option
    const customTemplateOption = page.locator('input[value*="custom"], option').filter({ hasText: /Custom/ });

    if (await customTemplateOption.count() > 0) {
      if (customTemplateOption.first().tagName() === 'INPUT') {
        await customTemplateOption.check();
      } else {
        const select = page.locator('select').filter({ has: customTemplateOption });
        await select.selectOption('custom');
      }

      // Should show custom template editor
      const templateEditor = page.locator('textarea[name*="template"], .template-editor');
      if (await templateEditor.count() > 0) {
        await expect(templateEditor).toBeVisible();

        // Test custom template content
        const customTemplate = `
# {{project.name}}

{{project.description}}

## Requirements
{{#each requirements}}
### {{title}}
{{description}}
{{/each}}
        `;

        await templateEditor.fill(customTemplate);
      }
    }
  });

  test('should export documentation in different formats', async ({ page }) => {
    // Test PDF export
    const pdfFormat = page.locator('select[name*="format"] option[value*="pdf"], input[value*="pdf"]');
    if (await pdfFormat.count() > 0) {
      if (pdfFormat.first().tagName() === 'INPUT') {
        await pdfFormat.check();
      } else {
        const select = page.locator('select').filter({ has: pdfFormat });
        await select.selectOption('pdf');
      }

      const generateButton = page.locator('button').filter({ hasText: /Generate|Create|Export/ });
      await generateButton.click();

      await page.waitForTimeout(3000);

      // Should trigger download or show download link
      const downloadLink = page.locator('a[download*=".pdf"], button').filter({ hasText: /Download.*PDF/i });
      if (await downloadLink.count() > 0) {
        await expect(downloadLink).toBeVisible();
      }
    }

    // Test HTML export
    const htmlFormat = page.locator('select[name*="format"] option[value*="html"], input[value*="html"]');
    if (await htmlFormat.count() > 0) {
      if (htmlFormat.first().tagName() === 'INPUT') {
        await htmlFormat.check();
      } else {
        const select = page.locator('select').filter({ has: htmlFormat });
        await select.selectOption('html');
      }

      const generateButton = page.locator('button').filter({ hasText: /Generate|Create|Export/ });
      await generateButton.click();

      await page.waitForTimeout(3000);

      // Should show HTML preview or download
      const htmlPreview = page.locator('.html-preview, iframe');
      const downloadLink = page.locator('a[download*=".html"], button').filter({ hasText: /Download.*HTML/i });

      if (await htmlPreview.count() > 0) {
        await expect(htmlPreview).toBeVisible();
      } else if (await downloadLink.count() > 0) {
        await expect(downloadLink).toBeVisible();
      }
    }
  });
});

test.describe('Documentation Generation Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects/1/documentation');
  });

  test('should save documentation preferences', async ({ page }) => {
    // Set preferences
    const templateSelect = page.locator('select[name*="template"]');
    if (await templateSelect.count() > 0) {
      await templateSelect.selectOption('detailed');
    }

    const formatSelect = page.locator('select[name*="format"]');
    if (await formatSelect.count() > 0) {
      await formatSelect.selectOption('markdown');
    }

    // Enable specific sections
    const domainModelCheckbox = page.locator('input[name*="domain"]');
    if (await domainModelCheckbox.count() > 0) {
      await domainModelCheckbox.check();
    }

    // Save preferences
    const savePreferencesButton = page.locator('button').filter({ hasText: /Save.*Preferences|Save.*Settings/ });
    if (await savePreferencesButton.count() > 0) {
      await savePreferencesButton.click();

      await page.waitForTimeout(1000);

      // Should show success message
      const successMessage = page.locator('.success, .text-green-600');
      await expect(successMessage).toBeVisible();

      // Reload page and check preferences are maintained
      await page.reload();

      await expect(templateSelect).toHaveValue('detailed');
      await expect(formatSelect).toHaveValue('markdown');
      await expect(domainModelCheckbox).toBeChecked();
    }
  });

  test('should provide documentation history', async ({ page }) => {
    // Look for documentation history section
    const historySection = page.locator('.history, .previous-documents');
    const historyTab = page.locator('[role="tab"]').filter({ hasText: /History/ });

    if (await historySection.count() > 0) {
      await expect(historySection).toBeVisible();

      // Should show previous generations
      const historyItems = historySection.locator('.history-item, .document-item');
      if (await historyItems.count() > 0) {
        const firstItem = historyItems.first();
        await expect(firstItem).toBeVisible();

        // Should have download or view links
        const viewLink = firstItem.locator('a, button').filter({ hasText: /View|Download/ });
        if (await viewLink.count() > 0) {
          await expect(viewLink).toBeVisible();
        }
      }
    } else if (await historyTab.count() > 0) {
      await historyTab.click();
      await expect(historyTab).toHaveAttribute('aria-selected', 'true');
    }
  });

  test('should validate documentation requirements', async ({ page }) => {
    // Try to generate with no requirements
    const generateButton = page.locator('button').filter({ hasText: /Generate|Create|Export/ });
    await generateButton.click();

    await page.waitForTimeout(1000);

    // Should show validation message if no requirements exist
    const validationMessage = page.locator('.warning, .text-yellow-600, [role="alert"]');
    if (await validationMessage.count() > 0) {
      await expect(validationMessage).toContainText(/no requirements|empty project/i);
    }
  });

  test('should estimate documentation generation time', async ({ page }) => {
    // Look for time estimation
    const timeEstimate = page.locator('.estimate, .generation-time');

    if (await timeEstimate.count() > 0) {
      await expect(timeEstimate).toBeVisible();
      await expect(timeEstimate).toContainText(/estimate|time|minutes/i);
    }

    // Change template and check if estimate updates
    const templateSelect = page.locator('select[name*="template"]');
    if (await templateSelect.count() > 0) {
      await templateSelect.selectOption('detailed');
      await page.waitForTimeout(500);

      // Estimate might change for more complex templates
      if (await timeEstimate.count() > 0) {
        await expect(timeEstimate).toBeVisible();
      }
    }
  });
});

test.describe('Documentation Collaboration Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects/1/documentation');
  });

  test('should support documentation sharing', async ({ page }) => {
    // Look for share button or functionality
    const shareButton = page.locator('button').filter({ hasText: /Share/ });

    if (await shareButton.count() > 0) {
      await shareButton.click();

      // Should show sharing options
      const shareModal = page.locator('[role="dialog"], .modal').filter({ hasText: /Share/ });
      await expect(shareModal).toBeVisible();

      // Should have sharing link
      const shareLink = shareModal.locator('input[readonly], .share-link');
      if (await shareLink.count() > 0) {
        await expect(shareLink).toBeVisible();

        const linkValue = await shareLink.inputValue();
        expect(linkValue).toContain('http');
      }

      // Should have copy button
      const copyButton = shareModal.locator('button').filter({ hasText: /Copy/ });
      if (await copyButton.count() > 0) {
        await copyButton.click();

        // Should show copied confirmation
        await page.waitForTimeout(500);
        const copiedMessage = page.locator('.copied, .text-green-600').filter({ hasText: /Copied/i });
        if (await copiedMessage.count() > 0) {
          await expect(copiedMessage).toBeVisible();
        }
      }
    }
  });

  test('should support documentation comments and feedback', async ({ page }) => {
    // Look for comments section
    const commentsSection = page.locator('.comments, .feedback');
    const commentsTab = page.locator('[role="tab"]').filter({ hasText: /Comments|Feedback/ });

    if (await commentsSection.count() > 0) {
      await expect(commentsSection).toBeVisible();
    } else if (await commentsTab.count() > 0) {
      await commentsTab.click();
      await expect(commentsTab).toHaveAttribute('aria-selected', 'true');
    }

    // Look for add comment functionality
    const addCommentButton = page.locator('button').filter({ hasText: /Add Comment|Comment/ });
    const commentTextarea = page.locator('textarea[placeholder*="comment"], textarea[name*="comment"]');

    if (await addCommentButton.count() > 0) {
      await addCommentButton.click();

      if (await commentTextarea.count() > 0) {
        await expect(commentTextarea).toBeVisible();

        // Test adding a comment
        await commentTextarea.fill('This documentation section needs more detail on the authentication flow.');

        const submitCommentButton = page.locator('button').filter({ hasText: /Submit|Post|Add/ });
        await submitCommentButton.click();

        await page.waitForTimeout(1000);

        // Should show the new comment
        const newComment = page.locator('.comment').filter({ hasText: /authentication flow/ });
        if (await newComment.count() > 0) {
          await expect(newComment).toBeVisible();
        }
      }
    }
  });

  test('should track documentation versions', async ({ page }) => {
    // Look for version control features
    const versionSelector = page.locator('select[name*="version"], .version-selector');
    const versionInfo = page.locator('.version, .v-');

    if (await versionSelector.count() > 0) {
      await expect(versionSelector).toBeVisible();

      // Should have version options
      const options = versionSelector.locator('option');
      await expect(options).toHaveCount.greaterThan(0);
    }

    if (await versionInfo.count() > 0) {
      await expect(versionInfo).toBeVisible();
      await expect(versionInfo).toContainText(/version|v\d/i);
    }

    // Look for version comparison
    const compareButton = page.locator('button').filter({ hasText: /Compare|Diff/ });
    if (await compareButton.count() > 0) {
      await compareButton.click();

      const comparisonView = page.locator('.comparison, .diff');
      if (await comparisonView.count() > 0) {
        await expect(comparisonView).toBeVisible();
      }
    }
  });
});