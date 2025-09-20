import { test, expect } from '@playwright/test';

test.describe('End-to-End Workflows', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin user for comprehensive workflow testing
    await page.goto('/login');
    await page.fill('#email', 'admin@example.com');
    await page.fill('#password', 'password123');
    await page.click('#login-button');
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test.describe('Complete Project Lifecycle', () => {
    test('should complete full project lifecycle from creation to delivery', async ({ page }) => {
      // Phase 1: Project Creation and Setup
      await page.goto('/projects');
      await page.click('button:has-text("New Project")');

      await page.fill('#project-name', 'E-commerce Platform');
      await page.fill('#project-description', 'Complete e-commerce platform with payment processing');
      await page.selectOption('#industry', 'retail');
      await page.selectOption('#project-type', 'web-application');
      await page.fill('#estimated-duration', '6');
      await page.selectOption('#priority', 'high');

      await page.click('button:has-text("Create Project")');
      await expect(page.locator('.success-message')).toContainText('Project created successfully');

      const projectUrl = page.url();
      const projectId = projectUrl.split('/').pop();

      // Phase 2: Team Setup and Role Assignment
      await page.click('tab:has-text("Team")');
      await page.click('button:has-text("Add Team Member")');

      await page.fill('#member-email', 'ba@example.com');
      await page.selectOption('#member-role', 'business-analyst');
      await page.click('button:has-text("Add Member")');

      await page.fill('#member-email', 'dev@example.com');
      await page.selectOption('#member-role', 'developer');
      await page.click('button:has-text("Add Member")');

      await expect(page.locator('.team-member')).toHaveCount(3); // Including admin

      // Phase 3: Requirements Gathering
      await page.click('tab:has-text("Requirements")');
      await page.click('button:has-text("New Requirement")');

      // Create multiple requirements
      const requirements = [
        {
          title: 'User Registration System',
          description: 'Users should be able to create accounts with email verification',
          type: 'functional',
          priority: 'high'
        },
        {
          title: 'Product Catalog Management',
          description: 'Admin should be able to manage product listings',
          type: 'functional',
          priority: 'high'
        },
        {
          title: 'Payment Processing',
          description: 'System should process payments securely via Stripe',
          type: 'functional',
          priority: 'critical'
        },
        {
          title: 'Performance Requirements',
          description: 'System should load pages within 2 seconds',
          type: 'non-functional',
          priority: 'medium'
        }
      ];

      for (const req of requirements) {
        await page.fill('#requirement-title', req.title);
        await page.fill('#requirement-description', req.description);
        await page.selectOption('#requirement-type', req.type);
        await page.selectOption('#priority', req.priority);
        await page.click('button:has-text("Create Requirement")');

        await expect(page.locator('.success-message')).toBeVisible();
        await page.click('button:has-text("New Requirement")');
      }

      // Phase 4: AI-Enhanced Requirements Analysis
      await page.click('button:has-text("Analyze with AI")');
      await expect(page.locator('.ai-analysis-results')).toBeVisible();

      // Generate acceptance criteria for critical requirement
      await page.click('.requirement-item:has-text("Payment Processing")');
      await page.click('button:has-text("Generate Acceptance Criteria")');
      await expect(page.locator('.acceptance-criteria')).toBeVisible();
      await expect(page.locator('.criteria-item')).toHaveCount.greaterThan(2);

      // Phase 5: Requirement Review and Approval
      await page.click('button:has-text("Submit for Review")');
      await page.selectOption('#reviewer', 'ba@example.com');
      await page.fill('#review-note', 'Please review requirements for completeness');
      await page.click('button:has-text("Submit")');

      // Simulate reviewer approval
      await page.goto('/profile');
      await page.click('button:has-text("Switch User")'); // Test helper
      await page.selectOption('#switch-to-user', 'ba@example.com');

      await page.goto(projectUrl);
      await page.click('tab:has-text("Requirements")');
      await page.click('.requirement-item:first-child .approve-button');
      await page.fill('#approval-comment', 'Requirements look comprehensive');
      await page.click('button:has-text("Approve")');

      // Phase 6: Project Planning and Estimation
      await page.click('tab:has-text("Planning")');
      await page.click('button:has-text("Generate Project Plan")');

      await expect(page.locator('.project-timeline')).toBeVisible();
      await expect(page.locator('.milestone-item')).toHaveCount.greaterThan(3);

      // Adjust timeline
      await page.click('.milestone-item:first-child .edit-button');
      await page.fill('#milestone-duration', '2');
      await page.click('button:has-text("Update")');

      // Phase 7: Implementation Tracking
      await page.click('tab:has-text("Progress")');
      await page.click('button:has-text("Start Implementation")');

      // Mark requirements as in-progress
      await page.click('.requirement-status[data-req="user-registration"] .status-select');
      await page.selectOption('.requirement-status[data-req="user-registration"] .status-select', 'in-progress');

      await page.click('.requirement-status[data-req="product-catalog"] .status-select');
      await page.selectOption('.requirement-status[data-req="product-catalog"] .status-select', 'completed');

      // Update progress
      await expect(page.locator('.progress-bar')).toHaveAttribute('data-progress', '50%');

      // Phase 8: Testing and Validation
      await page.click('tab:has-text("Testing")');
      await page.click('button:has-text("Generate Test Cases")');

      await expect(page.locator('.test-case')).toHaveCount.greaterThan(requirements.length);

      // Execute test cases
      await page.click('.test-case:first-child .execute-button');
      await page.selectOption('#test-result', 'passed');
      await page.fill('#test-notes', 'User registration works as expected');
      await page.click('button:has-text("Save Result")');

      // Phase 9: Deployment and Release
      await page.click('tab:has-text("Deployment")');
      await page.click('button:has-text("Prepare Release")');

      await page.fill('#release-version', '1.0.0');
      await page.fill('#release-notes', 'Initial release with core e-commerce functionality');
      await page.check('#all-tests-passed');
      await page.check('#security-review-completed');
      await page.click('button:has-text("Create Release")');

      // Phase 10: Project Completion
      await expect(page.locator('.release-success')).toContainText('Release 1.0.0 created successfully');

      await page.click('button:has-text("Mark Project Complete")');
      await page.fill('#completion-notes', 'Project delivered successfully on schedule');
      await page.click('button:has-text("Complete Project")');

      await expect(page.locator('.project-status')).toContainText('Completed');
      await expect(page.locator('.completion-certificate')).toBeVisible();
    });

    test('should handle project phase transitions and approvals', async ({ page }) => {
      // Create project
      await page.goto('/projects/new');
      await page.fill('#project-name', 'Phase Transition Test');
      await page.fill('#project-description', 'Testing phase transition workflow');
      await page.click('button:has-text("Create Project")');

      const projectUrl = page.url();

      // Phase 1: Planning -> Requirements
      await page.click('button:has-text("Move to Requirements Phase")');
      await expect(page.locator('.phase-transition-modal')).toBeVisible();

      await page.fill('#transition-reason', 'Planning completed, moving to requirements gathering');
      await page.check('#planning-deliverables-complete');
      await page.click('button:has-text("Confirm Transition")');

      await expect(page.locator('.current-phase')).toContainText('Requirements');

      // Phase 2: Requirements -> Design
      await page.click('button:has-text("Move to Design Phase")');
      await expect(page.locator('.transition-validation')).toBeVisible();
      await expect(page.locator('.validation-error')).toContainText('Minimum 3 requirements required');

      // Add required requirements
      await page.click('tab:has-text("Requirements")');
      for (let i = 1; i <= 3; i++) {
        await page.click('button:has-text("New Requirement")');
        await page.fill('#requirement-title', `Requirement ${i}`);
        await page.fill('#requirement-description', `Description for requirement ${i}`);
        await page.click('button:has-text("Create Requirement")');
      }

      // Try transition again
      await page.click('tab:has-text("Overview")');
      await page.click('button:has-text("Move to Design Phase")');
      await page.click('button:has-text("Confirm Transition")');

      await expect(page.locator('.current-phase')).toContainText('Design');

      // Phase 3: Design -> Implementation (with approval required)
      await page.click('button:has-text("Move to Implementation Phase")');
      await expect(page.locator('.approval-required')).toBeVisible();

      await page.fill('#approver-email', 'pm@example.com');
      await page.fill('#approval-request', 'Ready to start implementation phase');
      await page.click('button:has-text("Request Approval")');

      await expect(page.locator('.approval-pending')).toContainText('Approval pending from pm@example.com');
    });
  });

  test.describe('Requirements Lifecycle Workflow', () => {
    test('should complete requirements from creation to implementation', async ({ page }) => {
      // Setup project
      await page.goto('/projects');
      await page.click('.project-card:first-child');

      // Phase 1: Requirement Creation
      await page.click('tab:has-text("Requirements")');
      await page.click('button:has-text("New Requirement")');

      await page.fill('#requirement-title', 'User Authentication System');
      await page.fill('#requirement-description', 'Secure user authentication with multi-factor support');
      await page.selectOption('#requirement-type', 'functional');
      await page.selectOption('#priority', 'high');
      await page.selectOption('#complexity', 'medium');

      // Add stakeholders
      await page.fill('#primary-stakeholder', 'security@example.com');
      await page.fill('#secondary-stakeholders', 'product@example.com, dev@example.com');

      await page.click('button:has-text("Create Requirement")');
      await expect(page.locator('.requirement-id')).toContainText(/REQ-\d+/);

      const requirementUrl = page.url();

      // Phase 2: Requirement Enhancement with AI
      await page.click('button:has-text("Enhance with AI")');
      await page.selectOption('#enhancement-type', 'acceptance_criteria');
      await page.click('button:has-text("Generate")');

      await expect(page.locator('.ai-generated-criteria')).toBeVisible();
      await expect(page.locator('.criteria-item')).toHaveCount.greaterThan(3);

      // Accept AI suggestions
      await page.click('button:has-text("Accept All Suggestions")');
      await expect(page.locator('.acceptance-criteria-section')).toContainText(/Given.*When.*Then/);

      // Phase 3: Requirement Review Process
      await page.click('button:has-text("Submit for Review")');
      await page.selectOption('#review-type', 'technical');
      await page.selectOption('#reviewer', 'technical-lead@example.com');
      await page.fill('#review-deadline', '2024-12-31');
      await page.fill('#review-notes', 'Please review security aspects and implementation approach');
      await page.click('button:has-text("Submit")');

      await expect(page.locator('.requirement-status')).toContainText('Under Review');

      // Simulate reviewer feedback
      await page.goto('/profile');
      await page.click('button:has-text("Switch User")');
      await page.selectOption('#switch-to-user', 'technical-lead@example.com');

      await page.goto(requirementUrl);
      await page.click('button:has-text("Add Review Comments")');
      await page.fill('#review-comment', 'Consider adding OAuth 2.0 support for social login');
      await page.selectOption('#comment-type', 'suggestion');
      await page.click('button:has-text("Add Comment")');

      await page.click('button:has-text("Request Changes")');
      await page.fill('#change-summary', 'Add OAuth support and clarify MFA requirements');
      await page.click('button:has-text("Submit Review")');

      // Phase 4: Requirement Revision
      await page.goto('/profile');
      await page.click('button:has-text("Switch User")');
      await page.selectOption('#switch-to-user', 'admin@example.com');

      await page.goto(requirementUrl);
      await expect(page.locator('.requirement-status')).toContainText('Changes Requested');

      await page.click('button:has-text("Edit Requirement")');
      await page.fill('#requirement-description',
        'Secure user authentication with multi-factor support and OAuth 2.0 integration for social login'
      );

      // Add detailed acceptance criteria
      await page.click('button:has-text("Add Acceptance Criteria")');
      await page.fill('#new-criteria', 'Given user selects social login, When they authenticate via OAuth, Then they should be logged in successfully');
      await page.click('button:has-text("Add")');

      await page.click('button:has-text("Save Changes")');
      await page.click('button:has-text("Resubmit for Review")');

      // Phase 5: Final Approval
      await page.goto('/profile');
      await page.click('button:has-text("Switch User")');
      await page.selectOption('#switch-to-user', 'technical-lead@example.com');

      await page.goto(requirementUrl);
      await page.click('button:has-text("Approve Requirement")');
      await page.fill('#approval-comment', 'All security concerns addressed. Ready for implementation.');
      await page.selectOption('#approval-level', 'final');
      await page.click('button:has-text("Submit Approval")');

      await expect(page.locator('.requirement-status')).toContainText('Approved');

      // Phase 6: Implementation Planning
      await page.goto('/profile');
      await page.click('button:has-text("Switch User")');
      await page.selectOption('#switch-to-user', 'admin@example.com');

      await page.goto(requirementUrl);
      await page.click('button:has-text("Plan Implementation")');

      await page.fill('#estimated-hours', '40');
      await page.selectOption('#assigned-developer', 'dev@example.com');
      await page.fill('#implementation-notes', 'Use existing auth library, add OAuth provider integration');
      await page.fill('#target-sprint', 'Sprint 2024-Q1-3');

      await page.click('button:has-text("Create Implementation Plan")');
      await expect(page.locator('.implementation-plan')).toBeVisible();

      // Phase 7: Implementation Tracking
      await page.click('button:has-text("Start Implementation")');
      await expect(page.locator('.requirement-status')).toContainText('In Progress');

      // Track progress
      await page.fill('#progress-percentage', '25');
      await page.fill('#progress-notes', 'OAuth provider integration completed');
      await page.click('button:has-text("Update Progress")');

      await page.fill('#progress-percentage', '75');
      await page.fill('#progress-notes', 'MFA implementation in progress');
      await page.click('button:has-text("Update Progress")');

      await page.fill('#progress-percentage', '100');
      await page.fill('#progress-notes', 'Implementation completed, ready for testing');
      await page.click('button:has-text("Update Progress")');

      // Phase 8: Testing and Validation
      await page.click('button:has-text("Mark Ready for Testing")');
      await page.fill('#testing-notes', 'All acceptance criteria implemented');
      await page.click('button:has-text("Submit for Testing")');

      await expect(page.locator('.requirement-status')).toContainText('Testing');

      // Execute test cases
      await page.click('tab:has-text("Test Cases")');
      await expect(page.locator('.test-case')).toHaveCount.greaterThan(0);

      await page.click('.test-case:first-child .execute-button');
      await page.selectOption('#test-result', 'passed');
      await page.fill('#test-execution-notes', 'OAuth login works correctly');
      await page.click('button:has-text("Save Test Result")');

      // Phase 9: Final Verification and Closure
      await page.click('button:has-text("Mark as Completed")');
      await page.fill('#completion-verification', 'All test cases passed, requirement fully implemented');
      await page.check('#stakeholder-signoff');
      await page.click('button:has-text("Complete Requirement")');

      await expect(page.locator('.requirement-status')).toContainText('Completed');
      await expect(page.locator('.completion-certificate')).toBeVisible();
    });
  });

  test.describe('Multi-User Collaboration Workflows', () => {
    test('should handle concurrent collaboration between multiple team members', async ({ page, context }) => {
      // Setup project
      await page.goto('/projects');
      await page.click('.project-card:first-child');
      const projectUrl = page.url();

      // User 1 (Admin) creates requirement
      await page.click('tab:has-text("Requirements")');
      await page.click('button:has-text("New Requirement")');
      await page.fill('#requirement-title', 'Collaborative Editing Test');
      await page.fill('#requirement-description', 'Testing real-time collaboration');
      await page.click('button:has-text("Create Requirement")');

      const requirementUrl = page.url();

      // User 2 (Business Analyst) joins
      const baPage = await context.newPage();
      await baPage.goto('/login');
      await baPage.fill('#email', 'ba@example.com');
      await baPage.fill('#password', 'password123');
      await baPage.click('#login-button');
      await baPage.goto(requirementUrl);

      // User 3 (Developer) joins
      const devPage = await context.newPage();
      await devPage.goto('/login');
      await devPage.fill('#email', 'dev@example.com');
      await devPage.fill('#password', 'password123');
      await devPage.click('#login-button');
      await devPage.goto(requirementUrl);

      // Test real-time presence
      await expect(page.locator('.active-users')).toContainText('3 users active');
      await expect(page.locator('.user-avatar[data-user="ba@example.com"]')).toBeVisible();
      await expect(page.locator('.user-avatar[data-user="dev@example.com"]')).toBeVisible();

      // Test collaborative editing
      await page.click('button:has-text("Edit")');
      await baPage.click('button:has-text("Add Comment")');
      await devPage.click('button:has-text("View History")');

      // User 1 edits description
      await page.fill('#requirement-description', 'Updated description by admin');

      // User 2 adds acceptance criteria simultaneously
      await baPage.fill('#new-acceptance-criteria', 'Given user opens app, When they login, Then they see dashboard');
      await baPage.click('button:has-text("Add Criteria")');

      // Verify real-time updates
      await expect(page.locator('.acceptance-criteria')).toContainText('Given user opens app');
      await expect(baPage.locator('#requirement-description')).toContainValue('Updated description by admin');

      // Test conflict resolution
      await page.fill('#requirement-priority', 'high');
      await baPage.fill('#requirement-priority', 'critical');

      await page.click('button:has-text("Save")');
      await baPage.click('button:has-text("Save")');

      // Verify conflict resolution dialog
      await expect(baPage.locator('.conflict-resolution')).toBeVisible();
      await baPage.click('button:has-text("Accept Their Changes")');

      // Test comment thread
      await devPage.click('button:has-text("Add Comment")');
      await devPage.fill('#comment-text', 'Technical feasibility looks good');
      await devPage.click('button:has-text("Post Comment")');

      await page.click('.comment-thread .reply-button');
      await page.fill('#reply-text', 'Thanks for the technical review');
      await page.click('button:has-text("Post Reply")');

      // Verify all users see the comment thread
      await expect(baPage.locator('.comment-thread')).toContainText('Technical feasibility looks good');
      await expect(baPage.locator('.comment-thread')).toContainText('Thanks for the technical review');
    });

    test('should handle workflow approvals and notifications', async ({ page, context }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');

      // Create requirement needing approval
      await page.click('tab:has-text("Requirements")');
      await page.click('button:has-text("New Requirement")');
      await page.fill('#requirement-title', 'High-Value Feature Request');
      await page.fill('#requirement-description', 'Critical feature requiring multiple approvals');
      await page.selectOption('#priority', 'critical');
      await page.selectOption('#complexity', 'high');
      await page.click('button:has-text("Create Requirement")');

      // Submit for approval workflow
      await page.click('button:has-text("Submit for Approval")');
      await page.check('#require-business-approval');
      await page.check('#require-technical-approval');
      await page.check('#require-security-approval');

      await page.fill('#business-approver', 'pm@example.com');
      await page.fill('#technical-approver', 'tech-lead@example.com');
      await page.fill('#security-approver', 'security@example.com');

      await page.click('button:has-text("Submit for Approval")');

      // Verify approval workflow initiated
      await expect(page.locator('.approval-workflow')).toBeVisible();
      await expect(page.locator('.pending-approvals')).toContainText('3 approvals pending');

      // Business Manager approval
      const pmPage = await context.newPage();
      await pmPage.goto('/login');
      await pmPage.fill('#email', 'pm@example.com');
      await pmPage.fill('#password', 'password123');
      await pmPage.click('#login-button');

      await pmPage.goto('/notifications');
      await expect(pmPage.locator('.approval-notification')).toBeVisible();
      await pmPage.click('.approval-notification .review-button');

      await pmPage.click('button:has-text("Approve")');
      await pmPage.fill('#approval-comment', 'Business case is strong, approved');
      await pmPage.click('button:has-text("Submit Approval")');

      // Technical Lead approval
      const techPage = await context.newPage();
      await techPage.goto('/login');
      await techPage.fill('#email', 'tech-lead@example.com');
      await techPage.fill('#password', 'password123');
      await techPage.click('#login-button');

      await techPage.goto('/approvals');
      await techPage.click('.pending-approval:first-child .review-button');
      await techPage.click('button:has-text("Approve")');
      await techPage.fill('#approval-comment', 'Technical implementation is feasible');
      await techPage.click('button:has-text("Submit Approval")');

      // Security Team conditional approval
      const secPage = await context.newPage();
      await secPage.goto('/login');
      await secPage.fill('#email', 'security@example.com');
      await secPage.fill('#password', 'password123');
      await secPage.click('#login-button');

      await secPage.goto('/approvals');
      await secPage.click('.pending-approval:first-child .review-button');
      await secPage.click('button:has-text("Approve with Conditions")');
      await secPage.fill('#approval-comment', 'Approved pending security audit during implementation');
      await secPage.fill('#approval-conditions', 'Security audit required before production deployment');
      await secPage.click('button:has-text("Submit Approval")');

      // Verify all approvals received
      await page.reload();
      await expect(page.locator('.approval-status')).toContainText('Approved with Conditions');
      await expect(page.locator('.approval-conditions')).toContainText('Security audit required');

      // Test notification delivery
      await expect(page.locator('.notification-badge')).toContainText(/\d+/);
      await page.click('.notifications-bell');
      await expect(page.locator('.notification-item')).toContainText('All approvals received');
    });
  });

  test.describe('Integration and Data Flow Workflows', () => {
    test('should demonstrate complete data flow from requirements to implementation', async ({ page }) => {
      // Phase 1: Business Requirements to Technical Specifications
      await page.goto('/projects');
      await page.click('.project-card:first-child');

      await page.click('tab:has-text("Requirements")');
      await page.click('button:has-text("New Requirement")');

      // Business requirement
      await page.fill('#requirement-title', 'Customer Order Management');
      await page.fill('#requirement-description', 'Customers should be able to place, track, and modify orders');
      await page.selectOption('#requirement-type', 'business');
      await page.click('button:has-text("Create Requirement")');

      const businessReqUrl = page.url();

      // Convert to technical specifications
      await page.click('button:has-text("Generate Technical Specs")');
      await expect(page.locator('.tech-spec-generation')).toBeVisible();

      await page.check('#include-data-model');
      await page.check('#include-api-endpoints');
      await page.check('#include-security-requirements');
      await page.click('button:has-text("Generate")');

      // Verify technical specifications generated
      await expect(page.locator('.technical-specs')).toBeVisible();
      await expect(page.locator('.data-model-section')).toContainText(/Order.*Customer.*Product/);
      await expect(page.locator('.api-endpoints-section')).toContainText(/POST.*GET.*PUT.*DELETE/);

      // Phase 2: Technical Specs to Implementation Tasks
      await page.click('button:has-text("Create Implementation Tasks")');
      await expect(page.locator('.task-generation')).toBeVisible();

      await page.selectOption('#development-methodology', 'agile');
      await page.fill('#sprint-duration', '2');
      await page.selectOption('#team-size', 'medium');
      await page.click('button:has-text("Generate Tasks")');

      // Verify tasks created
      await expect(page.locator('.implementation-tasks')).toBeVisible();
      await expect(page.locator('.task-item')).toHaveCount.greaterThan(5);
      await expect(page.locator('.task-item')).toContainText(/Database schema.*API endpoints.*Frontend components/);

      // Phase 3: Task Assignment and Sprint Planning
      await page.click('button:has-text("Plan Sprints")');

      // Sprint 1
      await page.dragAndDrop('.task-item:has-text("Database schema")', '.sprint-1-tasks');
      await page.dragAndDrop('.task-item:has-text("Order model")', '.sprint-1-tasks');
      await page.dragAndDrop('.task-item:has-text("API endpoints")', '.sprint-1-tasks');

      // Sprint 2
      await page.dragAndDrop('.task-item:has-text("Frontend components")', '.sprint-2-tasks');
      await page.dragAndDrop('.task-item:has-text("Order tracking")', '.sprint-2-tasks');

      await page.click('button:has-text("Save Sprint Plan")');

      // Phase 4: Development Progress Tracking
      await page.click('tab:has-text("Progress")');

      // Simulate development progress
      await page.click('.task-item:first-child .start-button');
      await page.selectOption('.task-item:first-child .status-select', 'in-progress');

      await page.fill('.task-item:first-child .progress-input', '50');
      await page.fill('.task-item:first-child .notes-input', 'Database schema design completed');
      await page.click('.task-item:first-child .update-button');

      // Complete task
      await page.selectOption('.task-item:first-child .status-select', 'completed');
      await page.fill('.task-item:first-child .completion-notes', 'Database schema implemented and tested');
      await page.click('.task-item:first-child .update-button');

      // Phase 5: Testing Integration
      await page.click('tab:has-text("Testing")');
      await page.click('button:has-text("Generate Test Cases")');

      await expect(page.locator('.test-cases')).toBeVisible();
      await expect(page.locator('.test-case')).toContainText(/unit test.*integration test.*e2e test/);

      // Execute tests
      await page.click('.test-case:first-child .execute-button');
      await page.selectOption('#test-result', 'passed');
      await page.fill('#test-notes', 'Order creation API test passed');
      await page.click('button:has-text("Save Result")');

      // Phase 6: Deployment and Release
      await page.click('tab:has-text("Deployment")');
      await page.click('button:has-text("Create Release")');

      await page.fill('#release-version', '1.1.0');
      await page.fill('#release-notes', 'Added customer order management functionality');
      await page.check('#all-tests-passed');
      await page.check('#code-review-completed');
      await page.check('#security-scan-passed');

      await page.click('button:has-text("Deploy to Staging")');
      await expect(page.locator('.deployment-progress')).toBeVisible();

      // Phase 7: Stakeholder Validation
      await page.click('button:has-text("Request Stakeholder Validation")');
      await page.fill('#validation-instructions', 'Please test order placement and tracking functionality');
      await page.fill('#validation-criteria', 'Orders should be created, tracked, and modifiable as specified');
      await page.click('button:has-text("Send Validation Request")');

      // Phase 8: Requirements Traceability Report
      await page.click('button:has-text("Generate Traceability Report")');
      await expect(page.locator('.traceability-report')).toBeVisible();

      // Verify traceability links
      await expect(page.locator('.traceability-item')).toContainText(/Business Requirement.*Technical Spec.*Implementation Task.*Test Case/);
      await expect(page.locator('.coverage-metrics')).toContainText(/100% requirements coverage/);
    });

    test('should handle end-to-end audit trail and compliance tracking', async ({ page }) => {
      await page.goto('/projects');
      await page.click('.project-card:first-child');

      // Enable audit tracking
      await page.click('tab:has-text("Settings")');
      await page.check('#enable-audit-trail');
      await page.check('#enable-compliance-tracking');
      await page.selectOption('#compliance-standard', 'iso-27001');
      await page.click('button:has-text("Save Settings")');

      // Create requirement with compliance tracking
      await page.click('tab:has-text("Requirements")');
      await page.click('button:has-text("New Requirement")');

      await page.fill('#requirement-title', 'Data Privacy Compliance');
      await page.fill('#requirement-description', 'System must comply with GDPR data protection requirements');
      await page.selectOption('#compliance-category', 'data-protection');
      await page.selectOption('#regulatory-framework', 'gdpr');
      await page.click('button:has-text("Create Requirement")');

      // Verify audit trail created
      await page.click('tab:has-text("Audit Trail")');
      await expect(page.locator('.audit-entry')).toContainText('Requirement created');
      await expect(page.locator('.audit-entry')).toContainText('admin@example.com');

      // Make changes to track
      await page.click('tab:has-text("Requirements")');
      await page.click('.requirement-item:first-child .edit-button');
      await page.fill('#requirement-description',
        'System must comply with GDPR data protection requirements including right to be forgotten'
      );
      await page.click('button:has-text("Save Changes")');

      // Add compliance evidence
      await page.click('button:has-text("Add Compliance Evidence")');
      await page.fill('#evidence-type', 'Legal Review');
      await page.fill('#evidence-description', 'Legal team confirmed GDPR compliance approach');
      await page.setInputFiles('#evidence-file', {
        name: 'legal-review.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('Legal review document')
      });
      await page.click('button:has-text("Upload Evidence")');

      // Verify compliance tracking
      await page.click('tab:has-text("Compliance")');
      await expect(page.locator('.compliance-dashboard')).toBeVisible();
      await expect(page.locator('.compliance-status')).toContainText('Compliant');
      await expect(page.locator('.evidence-count')).toContainText('1 evidence file');

      // Generate compliance report
      await page.click('button:has-text("Generate Compliance Report")');
      await expect(page.locator('.report-generation')).toBeVisible();
      await expect(page.locator('.download-link')).toBeVisible({ timeout: 10000 });

      // Verify complete audit trail
      await page.click('tab:has-text("Audit Trail")');
      await expect(page.locator('.audit-entry')).toHaveCount.greaterThan(3);
      await expect(page.locator('.audit-entry')).toContainText(/created.*modified.*evidence added/);

      // Test audit search and filtering
      await page.fill('#audit-search', 'compliance');
      await page.click('button:has-text("Search Audit")');
      await expect(page.locator('.audit-entry')).toContainText('compliance');

      await page.selectOption('#audit-filter-action', 'evidence-added');
      await page.click('button:has-text("Apply Filter")');
      await expect(page.locator('.audit-entry')).toContainText('evidence added');
    });
  });
});