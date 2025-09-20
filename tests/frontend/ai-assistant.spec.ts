import { test, expect } from '@playwright/test';

test.describe('AI Assistant Features', () => {
  test.beforeEach(async ({ page }) => {
    // Login as authenticated user with AI access
    await page.goto('/login');
    await page.fill('#email', 'admin@example.com');
    await page.fill('#password', 'password123');
    await page.click('#login-button');
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test.describe('AI Conversation Management', () => {
    test('should create new AI conversation', async ({ page }) => {
      // Navigate to AI assistant
      await page.click('text=AI Assistant');
      await expect(page).toHaveURL(/.*\/ai/);

      // Create new conversation
      await page.click('button:has-text("New Conversation")');
      await expect(page.locator('.conversation-title')).toBeVisible();

      // Verify conversation is created
      await expect(page.locator('.conversation-id')).toContainText(/conv_/);
    });

    test('should send message to AI assistant', async ({ page }) => {
      // Navigate to AI conversations
      await page.goto('/ai/conversations');
      await page.click('button:has-text("New Conversation")');

      // Send message
      const messageInput = page.locator('#message-input');
      await messageInput.fill('Help me create requirements for a user authentication system');
      await page.click('button:has-text("Send")');

      // Verify message appears in conversation
      await expect(page.locator('.message-user')).toContainText('Help me create requirements');

      // Wait for AI response
      await expect(page.locator('.message-ai')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('.message-ai')).toContainText(/authentication|requirements/i);
    });

    test('should handle streaming AI responses', async ({ page }) => {
      await page.goto('/ai/conversations');
      await page.click('button:has-text("New Conversation")');

      // Send message that triggers streaming
      await page.fill('#message-input', 'Generate 10 detailed requirements for a payment system');
      await page.click('button:has-text("Send")');

      // Verify streaming indicator appears
      await expect(page.locator('.typing-indicator')).toBeVisible();

      // Wait for streaming to complete
      await expect(page.locator('.typing-indicator')).toBeHidden({ timeout: 15000 });

      // Verify complete response
      await expect(page.locator('.message-ai')).toContainText(/payment|requirements/i);
    });

    test('should display conversation history', async ({ page }) => {
      // Create conversation with multiple messages
      await page.goto('/ai/conversations');
      await page.click('button:has-text("New Conversation")');

      // Send first message
      await page.fill('#message-input', 'What is requirements engineering?');
      await page.click('button:has-text("Send")');
      await expect(page.locator('.message-ai')).toBeVisible();

      // Send second message
      await page.fill('#message-input', 'How do I write good acceptance criteria?');
      await page.click('button:has-text("Send")');
      await expect(page.locator('.message-ai').nth(1)).toBeVisible();

      // Verify conversation history
      expect(await page.locator('.message-user').count()).toBe(2);
      expect(await page.locator('.message-ai').count()).toBe(2);
    });

    test('should save and load conversations', async ({ page }) => {
      // Create a conversation
      await page.goto('/ai/conversations');
      await page.click('button:has-text("New Conversation")');

      await page.fill('#message-input', 'Test conversation for persistence');
      await page.click('button:has-text("Send")');
      await expect(page.locator('.message-ai')).toBeVisible();

      // Navigate away and back
      await page.goto('/dashboard');
      await page.goto('/ai/conversations');

      // Verify conversation is in history
      await expect(page.locator('.conversation-list')).toContainText('Test conversation');

      // Click on conversation to load it
      await page.click('.conversation-list-item:first-child');
      await expect(page.locator('.message-user')).toContainText('Test conversation for persistence');
    });
  });

  test.describe('AI-Powered Requirements Generation', () => {
    test('should generate requirements from natural language', async ({ page }) => {
      await page.goto('/ai/conversations');
      await page.click('button:has-text("New Conversation")');

      // Request requirements generation
      const prompt = 'I need a mobile app for ordering food with payment processing, user accounts, and restaurant management';
      await page.fill('#message-input', prompt);
      await page.click('button:has-text("Send")');

      // Wait for AI response
      await expect(page.locator('.message-ai')).toBeVisible({ timeout: 15000 });

      // Verify requirements structure
      const aiResponse = await page.locator('.message-ai').textContent();
      expect(aiResponse).toMatch(/user.*account|payment|restaurant|ordering/i);

      // Check for requirements format
      expect(aiResponse).toMatch(/requirement|shall|must|should/i);
    });

    test('should enhance existing requirements with AI', async ({ page }) => {
      // Navigate to requirements section
      await page.goto('/requirements');
      await page.click('button:has-text("New Requirement")');

      // Create basic requirement
      await page.fill('#requirement-title', 'User Login');
      await page.fill('#requirement-description', 'Users should be able to log in');
      await page.click('button:has-text("Enhance with AI")');

      // Wait for AI enhancement
      await expect(page.locator('.ai-enhancement-panel')).toBeVisible();
      await expect(page.locator('.enhanced-description')).toContainText(/authentication|security|validation/i);

      // Accept enhancement
      await page.click('button:has-text("Accept Enhancement")');
      await expect(page.locator('#requirement-description')).toContainText(/authentication|security/i);
    });

    test('should provide AI quality analysis', async ({ page }) => {
      await page.goto('/requirements');
      await page.click('button:has-text("New Requirement")');

      // Create requirement with quality issues
      await page.fill('#requirement-title', 'System should work');
      await page.fill('#requirement-description', 'The system should work well and be good');

      // Trigger AI analysis
      await page.click('button:has-text("Analyze Quality")');

      // Verify quality feedback
      await expect(page.locator('.quality-analysis')).toBeVisible();
      await expect(page.locator('.quality-score')).toBeVisible();
      await expect(page.locator('.quality-suggestions')).toContainText(/specific|measurable|clear/i);
    });

    test('should generate acceptance criteria with AI', async ({ page }) => {
      await page.goto('/requirements');
      await page.click('button:has-text("New Requirement")');

      await page.fill('#requirement-title', 'User Profile Management');
      await page.fill('#requirement-description', 'Users can view and edit their profile information');

      // Generate acceptance criteria
      await page.click('button:has-text("Generate Acceptance Criteria")');

      // Wait for AI generation
      await expect(page.locator('.acceptance-criteria')).toBeVisible({ timeout: 10000 });

      // Verify criteria format
      const criteria = await page.locator('.acceptance-criteria').textContent();
      expect(criteria).toMatch(/given|when|then|scenario/i);
      expect(criteria).toMatch(/profile|edit|view|user/i);
    });
  });

  test.describe('AI Template Management', () => {
    test('should display available conversation templates', async ({ page }) => {
      await page.goto('/ai/templates');

      // Verify template categories
      await expect(page.locator('.template-category')).toContainText(/Requirements Analysis|System Design|Quality Review/);

      // Check template previews
      await expect(page.locator('.template-preview')).toBeVisible();
    });

    test('should use template for conversation', async ({ page }) => {
      await page.goto('/ai/templates');

      // Select requirements analysis template
      await page.click('.template-item:has-text("Requirements Analysis")');
      await page.click('button:has-text("Use Template")');

      // Verify redirected to conversation with template
      await expect(page).toHaveURL(/.*\/ai\/conversations/);
      await expect(page.locator('#message-input')).toContainText(/requirements|analysis/i);
    });

    test('should customize AI model settings', async ({ page }) => {
      await page.goto('/ai/settings');

      // Verify model selection
      await expect(page.locator('#model-select')).toBeVisible();

      // Change temperature setting
      await page.fill('#temperature-input', '0.7');
      await page.click('button:has-text("Save Settings")');

      // Verify settings saved
      await expect(page.locator('.success-message')).toContainText('Settings saved');
    });
  });

  test.describe('AI Integration with Requirements', () => {
    test('should integrate AI suggestions into requirements workflow', async ({ page }) => {
      await page.goto('/requirements');

      // Start creating requirement
      await page.click('button:has-text("New Requirement")');
      await page.fill('#requirement-title', 'Payment Processing');

      // Get AI suggestions while typing
      await page.fill('#requirement-description', 'Process payments securely');
      await expect(page.locator('.ai-suggestions')).toBeVisible();

      // Click on AI suggestion
      await page.click('.ai-suggestion:first-child');

      // Verify suggestion applied
      await expect(page.locator('#requirement-description')).toContainText(/encryption|PCI|compliance/i);
    });

    test('should provide contextual AI help', async ({ page }) => {
      await page.goto('/requirements/new');

      // Activate AI help panel
      await page.click('.ai-help-toggle');
      await expect(page.locator('.ai-help-panel')).toBeVisible();

      // Get help for specific field
      await page.click('#requirement-priority');
      await expect(page.locator('.ai-help-content')).toContainText(/priority|importance|MoSCoW/i);
    });

    test('should validate requirements using AI', async ({ page }) => {
      await page.goto('/requirements');
      await page.click('button:has-text("New Requirement")');

      // Fill incomplete requirement
      await page.fill('#requirement-title', 'User Story');
      await page.fill('#requirement-description', 'As a user I want to do something');

      // Trigger AI validation
      await page.click('button:has-text("Validate")');

      // Check validation results
      await expect(page.locator('.validation-results')).toBeVisible();
      await expect(page.locator('.validation-error')).toContainText(/specific|clear|acceptance criteria/i);
    });
  });

  test.describe('AI Performance and Error Handling', () => {
    test('should handle AI service timeout gracefully', async ({ page }) => {
      // Mock slow AI response
      await page.route('**/api/ai/**', route => {
        setTimeout(() => route.continue(), 15000);
      });

      await page.goto('/ai/conversations');
      await page.click('button:has-text("New Conversation")');

      await page.fill('#message-input', 'Test timeout handling');
      await page.click('button:has-text("Send")');

      // Verify timeout handling
      await expect(page.locator('.error-message')).toContainText(/timeout|slow response/i, { timeout: 20000 });
    });

    test('should handle AI service errors', async ({ page }) => {
      // Mock AI service error
      await page.route('**/api/ai/**', route => {
        route.fulfill({ status: 500, body: 'AI service unavailable' });
      });

      await page.goto('/ai/conversations');
      await page.click('button:has-text("New Conversation")');

      await page.fill('#message-input', 'Test error handling');
      await page.click('button:has-text("Send")');

      // Verify error handling
      await expect(page.locator('.error-message')).toContainText(/unavailable|error/i);
      await expect(page.locator('button:has-text("Retry")')).toBeVisible();
    });

    test('should show loading states during AI processing', async ({ page }) => {
      await page.goto('/ai/conversations');
      await page.click('button:has-text("New Conversation")');

      await page.fill('#message-input', 'Generate complex requirements');
      await page.click('button:has-text("Send")');

      // Verify loading indicators
      await expect(page.locator('.ai-processing-indicator')).toBeVisible();
      await expect(page.locator('button:has-text("Send")')).toBeDisabled();

      // Wait for completion
      await expect(page.locator('.ai-processing-indicator')).toBeHidden({ timeout: 15000 });
      await expect(page.locator('button:has-text("Send")')).toBeEnabled();
    });
  });
});