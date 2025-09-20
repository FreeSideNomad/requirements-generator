import { test, expect } from '@playwright/test';

test.describe('User Management and RBAC', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin user with full user management permissions
    await page.goto('/login');
    await page.fill('#email', 'admin@example.com');
    await page.fill('#password', 'password123');
    await page.click('#login-button');
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test.describe('User Registration and Onboarding', () => {
    test('should register new user with email verification', async ({ page }) => {
      await page.goto('/register');

      // Fill registration form
      await page.fill('#first-name', 'John');
      await page.fill('#last-name', 'Doe');
      await page.fill('#email', 'john.doe@example.com');
      await page.fill('#password', 'SecurePass123!');
      await page.fill('#confirm-password', 'SecurePass123!');
      await page.selectOption('#department', 'engineering');
      await page.check('#terms-accepted');

      // Submit registration
      await page.click('#register-button');

      // Verify registration success
      await expect(page.locator('.registration-success')).toBeVisible();
      await expect(page.locator('.verification-notice')).toContainText(/verification email sent/i);

      // Simulate email verification
      await page.goto('/verify-email?token=mock-verification-token');
      await expect(page.locator('.verification-success')).toContainText('Email verified successfully');
    });

    test('should handle registration validation errors', async ({ page }) => {
      await page.goto('/register');

      // Test email validation
      await page.fill('#email', 'invalid-email');
      await page.click('#register-button');
      await expect(page.locator('.email-error')).toContainText(/invalid email format/i);

      // Test password strength validation
      await page.fill('#email', 'valid@example.com');
      await page.fill('#password', '123');
      await page.fill('#confirm-password', '123');
      await page.click('#register-button');
      await expect(page.locator('.password-error')).toContainText(/password too weak/i);

      // Test password confirmation mismatch
      await page.fill('#password', 'SecurePass123!');
      await page.fill('#confirm-password', 'DifferentPass123!');
      await page.click('#register-button');
      await expect(page.locator('.password-confirm-error')).toContainText(/passwords do not match/i);
    });

    test('should complete user onboarding flow', async ({ page }) => {
      // Start onboarding for new user
      await page.goto('/onboarding');

      // Step 1: Personal Information
      await page.fill('#job-title', 'Senior Requirements Analyst');
      await page.fill('#phone', '+1-555-0123');
      await page.selectOption('#timezone', 'America/New_York');
      await page.click('button:has-text("Next")');

      // Step 2: Role Selection
      await expect(page.locator('.role-selection')).toBeVisible();
      await page.click('.role-card[data-role="business-analyst"]');
      await expect(page.locator('.role-description')).toBeVisible();
      await page.click('button:has-text("Next")');

      // Step 3: Project Preferences
      await page.check('#interested-domains input[value="web-apps"]');
      await page.check('#interested-domains input[value="mobile-apps"]');
      await page.selectOption('#experience-level', 'intermediate');
      await page.click('button:has-text("Next")');

      // Step 4: Notification Preferences
      await page.check('#email-notifications');
      await page.uncheck('#sms-notifications');
      await page.selectOption('#digest-frequency', 'weekly');
      await page.click('button:has-text("Complete Onboarding")');

      // Verify onboarding completion
      await expect(page.locator('.onboarding-success')).toBeVisible();
      await expect(page).toHaveURL(/.*\/dashboard/);
    });
  });

  test.describe('User Profile Management', () => {
    test('should view and edit user profile', async ({ page }) => {
      await page.goto('/profile');

      // Verify profile sections
      await expect(page.locator('.profile-overview')).toBeVisible();
      await expect(page.locator('.contact-information')).toBeVisible();
      await expect(page.locator('.security-settings')).toBeVisible();
      await expect(page.locator('.notification-preferences')).toBeVisible();

      // Edit profile information
      await page.click('button:has-text("Edit Profile")');
      await page.fill('#bio', 'Experienced requirements analyst with 10+ years in software development.');
      await page.fill('#linkedin-url', 'https://linkedin.com/in/johndoe');
      await page.selectOption('#preferred-language', 'en');
      await page.click('button:has-text("Save Changes")');

      // Verify profile updated
      await expect(page.locator('.profile-success')).toContainText('Profile updated successfully');
      await expect(page.locator('.bio-text')).toContainText('Experienced requirements analyst');
    });

    test('should change user password', async ({ page }) => {
      await page.goto('/profile/security');

      // Change password
      await page.fill('#current-password', 'password123');
      await page.fill('#new-password', 'NewSecurePass456!');
      await page.fill('#confirm-new-password', 'NewSecurePass456!');
      await page.click('button:has-text("Change Password")');

      // Verify password changed
      await expect(page.locator('.password-success')).toContainText('Password updated successfully');

      // Test new password login
      await page.click('button:has-text("Logout")');
      await page.goto('/login');
      await page.fill('#email', 'admin@example.com');
      await page.fill('#password', 'NewSecurePass456!');
      await page.click('#login-button');
      await expect(page).toHaveURL(/.*\/dashboard/);
    });

    test('should configure two-factor authentication', async ({ page }) => {
      await page.goto('/profile/security');

      // Enable 2FA
      await page.click('button:has-text("Enable 2FA")');
      await expect(page.locator('.2fa-setup')).toBeVisible();

      // View QR code and backup codes
      await expect(page.locator('.qr-code')).toBeVisible();
      await expect(page.locator('.backup-codes')).toBeVisible();

      // Verify 2FA setup with test code
      await page.fill('#verification-code', '123456');
      await page.click('button:has-text("Verify and Enable")');

      // Verify 2FA enabled
      await expect(page.locator('.2fa-success')).toContainText('Two-factor authentication enabled');
      await expect(page.locator('.2fa-status')).toContainText('Enabled');

      // Test 2FA login
      await page.click('button:has-text("Logout")');
      await page.goto('/login');
      await page.fill('#email', 'admin@example.com');
      await page.fill('#password', 'NewSecurePass456!');
      await page.click('#login-button');

      // 2FA challenge
      await expect(page.locator('.2fa-challenge')).toBeVisible();
      await page.fill('#2fa-code', '123456');
      await page.click('button:has-text("Verify")');
      await expect(page).toHaveURL(/.*\/dashboard/);
    });

    test('should manage user sessions and devices', async ({ page }) => {
      await page.goto('/profile/sessions');

      // View active sessions
      await expect(page.locator('.sessions-list')).toBeVisible();
      await expect(page.locator('.current-session')).toBeVisible();
      await expect(page.locator('.session-item')).toHaveCount.greaterThan(0);

      // Check session details
      await expect(page.locator('.session-device')).toContainText(/Chrome|Firefox|Safari/);
      await expect(page.locator('.session-location')).toBeVisible();
      await expect(page.locator('.session-last-active')).toBeVisible();

      // Revoke a session
      await page.click('.session-item:not(.current-session) .revoke-button');
      await page.click('button:has-text("Confirm Revoke")');
      await expect(page.locator('.session-revoked')).toContainText('Session revoked successfully');

      // Revoke all other sessions
      await page.click('button:has-text("Revoke All Other Sessions")');
      await page.click('button:has-text("Confirm Revoke All")');
      await expect(page.locator('.sessions-cleared')).toContainText('All other sessions revoked');
    });
  });

  test.describe('Role-Based Access Control (RBAC)', () => {
    test('should view and manage user roles', async ({ page }) => {
      await page.goto('/admin/users');

      // View users list with roles
      await expect(page.locator('.users-table')).toBeVisible();
      await expect(page.locator('.user-role')).toBeVisible();

      // Edit user role
      await page.click('.user-row:first-child .edit-role-button');
      await expect(page.locator('.role-editor')).toBeVisible();

      // View available roles
      await expect(page.locator('.role-option[data-role="admin"]')).toBeVisible();
      await expect(page.locator('.role-option[data-role="project-manager"]')).toBeVisible();
      await expect(page.locator('.role-option[data-role="business-analyst"]')).toBeVisible();
      await expect(page.locator('.role-option[data-role="stakeholder"]')).toBeVisible();

      // Change user role
      await page.click('.role-option[data-role="project-manager"]');
      await expect(page.locator('.role-permissions-preview')).toBeVisible();
      await page.click('button:has-text("Update Role")');

      // Verify role updated
      await expect(page.locator('.role-success')).toContainText('User role updated');
      await expect(page.locator('.user-row:first-child .user-role')).toContainText('Project Manager');
    });

    test('should test permission-based access controls', async ({ page, context }) => {
      // Test admin permissions
      await page.goto('/admin/tenants');
      await expect(page.locator('.tenant-management')).toBeVisible();

      // Switch to limited user
      const limitedUserPage = await context.newPage();
      await limitedUserPage.goto('/login');
      await limitedUserPage.fill('#email', 'user@example.com');
      await limitedUserPage.fill('#password', 'password123');
      await limitedUserPage.click('#login-button');

      // Test restricted access
      await limitedUserPage.goto('/admin/tenants');
      await expect(limitedUserPage.locator('.access-denied')).toBeVisible();
      await expect(limitedUserPage.locator('.insufficient-permissions')).toContainText(/admin access required/i);

      // Test allowed access
      await limitedUserPage.goto('/projects');
      await expect(limitedUserPage.locator('.projects-list')).toBeVisible();
    });

    test('should manage custom roles and permissions', async ({ page }) => {
      await page.goto('/admin/roles');

      // Create custom role
      await page.click('button:has-text("Create Custom Role")');
      await page.fill('#role-name', 'Requirements Reviewer');
      await page.fill('#role-description', 'Can review and approve requirements but not edit projects');

      // Configure permissions
      await page.check('#permission-view-projects');
      await page.check('#permission-view-requirements');
      await page.check('#permission-approve-requirements');
      await page.uncheck('#permission-edit-projects');
      await page.uncheck('#permission-delete-requirements');

      // Save custom role
      await page.click('button:has-text("Create Role")');
      await expect(page.locator('.role-created')).toContainText('Custom role created successfully');

      // Assign custom role to user
      await page.goto('/admin/users');
      await page.click('.user-row:first-child .edit-role-button');
      await page.click('.role-option[data-role="requirements-reviewer"]');
      await page.click('button:has-text("Update Role")');

      // Verify custom role assignment
      await expect(page.locator('.user-role')).toContainText('Requirements Reviewer');
    });

    test('should handle role inheritance and hierarchies', async ({ page }) => {
      await page.goto('/admin/roles/hierarchy');

      // View role hierarchy
      await expect(page.locator('.role-hierarchy')).toBeVisible();
      await expect(page.locator('.role-level[data-level="1"]')).toContainText('Admin');
      await expect(page.locator('.role-level[data-level="2"]')).toContainText('Project Manager');
      await expect(page.locator('.role-level[data-level="3"]')).toContainText('Business Analyst');

      // Test permission inheritance
      await page.click('.role-card[data-role="project-manager"]');
      await expect(page.locator('.inherited-permissions')).toBeVisible();
      await expect(page.locator('.direct-permissions')).toBeVisible();

      // Modify role inheritance
      await page.click('button:has-text("Edit Inheritance")');
      await page.check('#inherit-from-business-analyst');
      await page.click('button:has-text("Save Inheritance")');

      // Verify inheritance updated
      await expect(page.locator('.inheritance-success')).toContainText('Role inheritance updated');
    });
  });

  test.describe('User Administration', () => {
    test('should manage user accounts from admin panel', async ({ page }) => {
      await page.goto('/admin/users');

      // View users overview
      await expect(page.locator('.users-stats')).toBeVisible();
      await expect(page.locator('.total-users')).toContainText(/\d+/);
      await expect(page.locator('.active-users')).toContainText(/\d+/);
      await expect(page.locator('.pending-users')).toContainText(/\d+/);

      // Filter users
      await page.selectOption('#filter-role', 'business-analyst');
      await page.selectOption('#filter-status', 'active');
      await page.fill('#search-users', 'john');
      await page.click('button:has-text("Apply Filters")');

      // Verify filtered results
      await expect(page.locator('.filter-results')).toContainText(/\d+ users found/);
      await expect(page.locator('.user-row')).toContainText(/john/i);
    });

    test('should suspend and reactivate user accounts', async ({ page }) => {
      await page.goto('/admin/users');
      await page.click('.user-row:first-child .actions-menu');

      // Suspend user
      await page.click('text=Suspend User');
      await expect(page.locator('.suspension-modal')).toBeVisible();

      await page.selectOption('#suspension-reason', 'policy-violation');
      await page.fill('#suspension-note', 'Violated company policy on data handling');
      await page.fill('#suspension-duration', '30');
      await page.click('button:has-text("Confirm Suspension")');

      // Verify user suspended
      await expect(page.locator('.suspension-success')).toContainText('User suspended successfully');
      await expect(page.locator('.user-status')).toContainText('Suspended');

      // Test suspended user login attempt
      await page.goto('/login');
      await page.fill('#email', 'suspended@example.com');
      await page.fill('#password', 'password123');
      await page.click('#login-button');
      await expect(page.locator('.account-suspended')).toContainText(/account has been suspended/i);

      // Reactivate user
      await page.goto('/admin/users');
      await page.click('.user-row[data-status="suspended"] .actions-menu');
      await page.click('text=Reactivate User');
      await page.fill('#reactivation-note', 'User completed training, reactivating account');
      await page.click('button:has-text("Confirm Reactivation")');

      // Verify user reactivated
      await expect(page.locator('.reactivation-success')).toContainText('User reactivated');
      await expect(page.locator('.user-status')).toContainText('Active');
    });

    test('should bulk manage users', async ({ page }) => {
      await page.goto('/admin/users');

      // Select multiple users
      await page.check('.user-row:nth-child(1) .user-checkbox');
      await page.check('.user-row:nth-child(2) .user-checkbox');
      await page.check('.user-row:nth-child(3) .user-checkbox');

      // Access bulk actions
      await page.click('button:has-text("Bulk Actions")');
      await expect(page.locator('.bulk-actions-menu')).toBeVisible();

      // Test bulk role assignment
      await page.click('text=Assign Role');
      await page.selectOption('#bulk-role', 'business-analyst');
      await page.click('button:has-text("Apply to Selected")');

      // Verify bulk update
      await expect(page.locator('.bulk-success')).toContainText('3 users updated');
      await expect(page.locator('.selected-users .user-role')).toContainText('Business Analyst');

      // Test bulk email notification
      await page.click('button:has-text("Bulk Actions")');
      await page.click('text=Send Notification');
      await page.fill('#notification-subject', 'System Maintenance Notice');
      await page.fill('#notification-message', 'Scheduled maintenance on Saturday night.');
      await page.click('button:has-text("Send to Selected")');

      // Verify notifications sent
      await expect(page.locator('.notification-success')).toContainText('Notifications sent to 3 users');
    });

    test('should export user data and reports', async ({ page }) => {
      await page.goto('/admin/users/reports');

      // Generate user activity report
      await page.selectOption('#report-type', 'user-activity');
      await page.fill('#date-from', '2024-01-01');
      await page.fill('#date-to', '2024-12-31');
      await page.check('#include-login-history');
      await page.check('#include-project-activity');
      await page.selectOption('#export-format', 'csv');

      await page.click('button:has-text("Generate Report")');

      // Verify report generation
      await expect(page.locator('.report-progress')).toBeVisible();
      await expect(page.locator('.download-link')).toBeVisible({ timeout: 30000 });

      // Test user data export for GDPR compliance
      await page.goto('/admin/users');
      await page.click('.user-row:first-child .actions-menu');
      await page.click('text=Export User Data');

      await page.check('#include-profile-data');
      await page.check('#include-activity-logs');
      await page.check('#include-project-history');
      await page.selectOption('#export-format', 'json');
      await page.click('button:has-text("Export Data")');

      // Verify GDPR export
      await expect(page.locator('.export-success')).toContainText('User data exported');
      await expect(page.locator('.gdpr-compliance')).toContainText('GDPR compliant export');
    });
  });

  test.describe('Team and Group Management', () => {
    test('should create and manage teams', async ({ page }) => {
      await page.goto('/admin/teams');

      // Create new team
      await page.click('button:has-text("Create Team")');
      await page.fill('#team-name', 'Requirements Analysis Team');
      await page.fill('#team-description', 'Team responsible for gathering and analyzing requirements');
      await page.selectOption('#team-department', 'product');
      await page.fill('#team-lead', 'john.doe@example.com');

      await page.click('button:has-text("Create Team")');

      // Verify team created
      await expect(page.locator('.team-success')).toContainText('Team created successfully');
      await expect(page.locator('.team-card')).toContainText('Requirements Analysis Team');

      // Add team members
      await page.click('.team-card:first-child');
      await page.click('button:has-text("Add Members")');

      await page.fill('#member-search', 'jane.smith@example.com');
      await page.click('.user-suggestion:first-child');
      await page.selectOption('#member-role', 'member');
      await page.click('button:has-text("Add Member")');

      // Verify member added
      await expect(page.locator('.team-members')).toContainText('jane.smith@example.com');
      await expect(page.locator('.member-count')).toContainText('2 members');
    });

    test('should manage team permissions and access', async ({ page }) => {
      await page.goto('/admin/teams');
      await page.click('.team-card:first-child');

      // Configure team permissions
      await page.click('tab:has-text("Permissions")');
      await expect(page.locator('.team-permissions')).toBeVisible();

      // Project access permissions
      await page.check('#team-can-create-projects');
      await page.check('#team-can-manage-requirements');
      await page.uncheck('#team-can-delete-projects');

      // Resource access permissions
      await page.check('#team-access-shared-templates');
      await page.check('#team-access-team-analytics');

      // Save permissions
      await page.click('button:has-text("Save Permissions")');
      await expect(page.locator('.permissions-success')).toContainText('Team permissions updated');

      // Test team-based project access
      await page.goto('/projects');
      await page.click('button:has-text("New Project")');
      await page.selectOption('#project-team', 'requirements-analysis-team');
      await expect(page.locator('.team-members-preview')).toBeVisible();
    });

    test('should handle team member roles and hierarchy', async ({ page }) => {
      await page.goto('/admin/teams');
      await page.click('.team-card:first-child');
      await page.click('tab:has-text("Members")');

      // View team hierarchy
      await expect(page.locator('.team-hierarchy')).toBeVisible();
      await expect(page.locator('.team-lead')).toBeVisible();
      await expect(page.locator('.team-members')).toBeVisible();

      // Change member role
      await page.click('.member-row:first-child .edit-role-button');
      await page.selectOption('#member-team-role', 'co-lead');
      await page.click('button:has-text("Update Role")');

      // Verify role updated
      await expect(page.locator('.member-role')).toContainText('Co-Lead');

      // Transfer team leadership
      await page.click('.team-lead .transfer-leadership');
      await page.selectOption('#new-lead', 'jane.smith@example.com');
      await page.fill('#transfer-reason', 'Organizational restructuring');
      await page.click('button:has-text("Transfer Leadership")');

      // Verify leadership transferred
      await expect(page.locator('.leadership-success')).toContainText('Team leadership transferred');
      await expect(page.locator('.team-lead')).toContainText('jane.smith@example.com');
    });
  });

  test.describe('Security and Audit', () => {
    test('should track user activity and audit logs', async ({ page }) => {
      await page.goto('/admin/audit-logs');

      // View audit log dashboard
      await expect(page.locator('.audit-dashboard')).toBeVisible();
      await expect(page.locator('.recent-activities')).toBeVisible();
      await expect(page.locator('.security-events')).toBeVisible();

      // Filter audit logs
      await page.selectOption('#log-category', 'authentication');
      await page.selectOption('#log-level', 'warning');
      await page.fill('#date-range-from', '2024-01-01');
      await page.fill('#date-range-to', '2024-12-31');
      await page.click('button:has-text("Apply Filters")');

      // Verify filtered logs
      await expect(page.locator('.audit-entry')).toContainText(/login|authentication|security/i);

      // View detailed audit entry
      await page.click('.audit-entry:first-child');
      await expect(page.locator('.audit-details')).toBeVisible();
      await expect(page.locator('.event-metadata')).toBeVisible();
      await expect(page.locator('.user-context')).toBeVisible();
    });

    test('should detect and handle suspicious activity', async ({ page }) => {
      await page.goto('/admin/security/alerts');

      // View security alerts
      await expect(page.locator('.security-alerts')).toBeVisible();
      await expect(page.locator('.alert-summary')).toBeVisible();

      // Check alert types
      await expect(page.locator('.alert-type-login-anomaly')).toBeVisible();
      await expect(page.locator('.alert-type-permission-escalation')).toBeVisible();
      await expect(page.locator('.alert-type-bulk-actions')).toBeVisible();

      // Investigate security alert
      await page.click('.security-alert:first-child');
      await expect(page.locator('.alert-investigation')).toBeVisible();
      await expect(page.locator('.event-timeline')).toBeVisible();
      await expect(page.locator('.affected-resources')).toBeVisible();

      // Take security action
      await page.click('button:has-text("Take Action")');
      await page.selectOption('#security-action', 'suspend-user');
      await page.fill('#action-reason', 'Suspicious login activity detected');
      await page.click('button:has-text("Execute Action")');

      // Verify security action taken
      await expect(page.locator('.action-success')).toContainText('Security action executed');
    });

    test('should manage API access and tokens', async ({ page }) => {
      await page.goto('/profile/api-access');

      // Create API token
      await page.click('button:has-text("Generate API Token")');
      await page.fill('#token-name', 'Requirements API Access');
      await page.fill('#token-description', 'Token for automated requirements management');

      // Configure token permissions
      await page.check('#permission-read-projects');
      await page.check('#permission-create-requirements');
      await page.uncheck('#permission-delete-projects');

      // Set token expiration
      await page.selectOption('#token-expiry', '90-days');
      await page.click('button:has-text("Generate Token")');

      // Verify token created
      await expect(page.locator('.token-success')).toContainText('API token generated');
      await expect(page.locator('.token-value')).toBeVisible();
      await expect(page.locator('.token-warning')).toContainText(/save this token|will not be shown again/i);

      // Test token management
      await page.click('.api-token:first-child .manage-button');
      await expect(page.locator('.token-details')).toBeVisible();
      await expect(page.locator('.token-usage-stats')).toBeVisible();

      // Revoke token
      await page.click('button:has-text("Revoke Token")');
      await page.click('button:has-text("Confirm Revoke")');
      await expect(page.locator('.token-revoked')).toContainText('API token revoked');
    });
  });

  test.describe('Error Handling and Edge Cases', () => {
    test('should handle user account conflicts and duplicates', async ({ page }) => {
      await page.goto('/register');

      // Try to register with existing email
      await page.fill('#email', 'admin@example.com'); // Existing user
      await page.fill('#password', 'NewPassword123!');
      await page.fill('#confirm-password', 'NewPassword123!');
      await page.click('#register-button');

      // Verify conflict handling
      await expect(page.locator('.email-conflict')).toContainText(/email already registered/i);
      await expect(page.locator('.suggested-actions')).toBeVisible();
      await expect(page.locator('button:has-text("Login Instead")')).toBeVisible();
      await expect(page.locator('button:has-text("Reset Password")')).toBeVisible();
    });

    test('should handle role assignment conflicts', async ({ page }) => {
      await page.goto('/admin/users');
      await page.click('.user-row:first-child .edit-role-button');

      // Mock role conflict scenario
      await page.route('**/api/users/*/role', route => {
        route.fulfill({
          status: 409,
          body: JSON.stringify({ error: 'Role assignment conflict' })
        });
      });

      await page.click('.role-option[data-role="admin"]');
      await page.click('button:has-text("Update Role")');

      // Verify conflict handling
      await expect(page.locator('.role-conflict')).toContainText(/role assignment conflict/i);
      await expect(page.locator('.conflict-resolution')).toBeVisible();
      await expect(page.locator('button:has-text("Force Update")')).toBeVisible();
      await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
    });

    test('should handle session timeouts and concurrent access', async ({ page, context }) => {
      // Simulate session timeout
      await page.route('**/api/auth/verify', route => {
        route.fulfill({ status: 401, body: 'Session expired' });
      });

      await page.goto('/admin/users');

      // Verify session timeout handling
      await expect(page.locator('.session-expired')).toBeVisible();
      await expect(page.locator('button:has-text("Login Again")')).toBeVisible();

      // Test concurrent session conflict
      const page2 = await context.newPage();
      await page2.goto('/login');
      await page2.fill('#email', 'admin@example.com');
      await page2.fill('#password', 'password123');
      await page2.click('#login-button');

      // Original session should be invalidated
      await page.goto('/admin/users');
      await expect(page.locator('.concurrent-session-warning')).toBeVisible();
    });
  });
});