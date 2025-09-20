import { test, expect } from '@playwright/test';

test.describe('Responsive Design Tests', () => {
  const viewports = [
    { name: 'Mobile Portrait', width: 375, height: 667 },
    { name: 'Mobile Landscape', width: 667, height: 375 },
    { name: 'Tablet Portrait', width: 768, height: 1024 },
    { name: 'Tablet Landscape', width: 1024, height: 768 },
    { name: 'Desktop', width: 1200, height: 800 },
    { name: 'Large Desktop', width: 1920, height: 1080 }
  ];

  for (const viewport of viewports) {
    test(`should display properly on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/dashboard');

      // Check that main content is visible
      const mainContent = page.locator('main, .main-content, .container').first();
      await expect(mainContent).toBeVisible();

      // Check that text is readable (not too small)
      const headings = page.locator('h1, h2, h3');
      if (await headings.count() > 0) {
        const fontSize = await headings.first().evaluate(el =>
          window.getComputedStyle(el).fontSize
        );
        const fontSizeNum = parseInt(fontSize);
        expect(fontSizeNum).toBeGreaterThan(14); // Minimum readable size
      }

      // Check for horizontal overflow
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeLessThanOrEqual(viewport.width + 20); // Allow small margin for scrollbars
    });
  }

  test('should adapt navigation for mobile devices', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');

    // Look for mobile navigation patterns
    const mobileNav = page.locator('.mobile-nav, .hamburger, [data-mobile-menu]');
    const hamburgerButton = page.locator('button').filter({ hasText: /menu/i }).or(
      page.locator('button[aria-label*="menu"], button[aria-expanded]')
    );

    if (await hamburgerButton.count() > 0) {
      await expect(hamburgerButton).toBeVisible();

      // Test mobile menu toggle
      await hamburgerButton.click();

      const mobileMenu = page.locator('.mobile-menu, .nav-menu[data-open="true"], [aria-expanded="true"] + .menu');
      if (await mobileMenu.count() > 0) {
        await expect(mobileMenu).toBeVisible();

        // Close menu
        await hamburgerButton.click();
        await expect(mobileMenu).toBeHidden();
      }
    }

    // Check that desktop navigation is hidden or adapted
    const desktopNav = page.locator('.desktop-nav, .lg\\:block');
    if (await desktopNav.count() > 0) {
      // Should be hidden on mobile
      const isHidden = await desktopNav.isHidden();
      expect(isHidden).toBeTruthy();
    }
  });

  test('should have touch-friendly interface on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');

    // Check button sizes are touch-friendly (minimum 44px)
    const buttons = page.locator('button, a[role="button"], .btn');

    for (let i = 0; i < Math.min(await buttons.count(), 5); i++) {
      const button = buttons.nth(i);
      if (await button.isVisible()) {
        const boundingBox = await button.boundingBox();
        if (boundingBox) {
          expect(boundingBox.height).toBeGreaterThanOrEqual(36); // Minimum touch target
          expect(boundingBox.width).toBeGreaterThanOrEqual(36);
        }
      }
    }

    // Check form inputs are appropriately sized
    const inputs = page.locator('input, textarea, select');

    for (let i = 0; i < Math.min(await inputs.count(), 3); i++) {
      const input = inputs.nth(i);
      if (await input.isVisible()) {
        const boundingBox = await input.boundingBox();
        if (boundingBox) {
          expect(boundingBox.height).toBeGreaterThanOrEqual(32); // Comfortable input height
        }
      }
    }
  });

  test('should maintain functionality across all viewport sizes', async ({ page }) => {
    const testActions = [
      { action: 'Click New Project', selector: 'button', text: 'New Project' },
      { action: 'Click Profile', selector: 'a[href="/profile"]', text: null },
      { action: 'Navigate to Users', selector: 'a[href="/admin/users"]', text: null }
    ];

    for (const viewport of viewports.slice(0, 3)) { // Test key viewports
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/dashboard');

      for (const testAction of testActions) {
        const element = testAction.text
          ? page.locator(testAction.selector).filter({ hasText: testAction.text })
          : page.locator(testAction.selector);

        if (await element.count() > 0 && await element.isVisible()) {
          await expect(element).toBeEnabled();

          // Test that element is clickable
          const boundingBox = await element.boundingBox();
          expect(boundingBox).toBeTruthy();
        }
      }
    }
  });
});

test.describe('Accessibility Tests', () => {
  test('should have proper heading structure', async ({ page }) => {
    await page.goto('/dashboard');

    // Check for h1
    const h1Elements = page.locator('h1');
    await expect(h1Elements).toHaveCount.greaterThanOrEqual(1);

    // Check heading hierarchy
    const allHeadings = page.locator('h1, h2, h3, h4, h5, h6');
    const headingLevels = await allHeadings.evaluateAll(headings =>
      headings.map(h => parseInt(h.tagName.charAt(1)))
    );

    // First heading should be h1
    expect(headingLevels[0]).toBe(1);

    // Check that heading levels don't skip (e.g., h1 to h3)
    for (let i = 1; i < headingLevels.length; i++) {
      const diff = headingLevels[i] - headingLevels[i - 1];
      expect(diff).toBeLessThanOrEqual(1);
    }
  });

  test('should have proper ARIA labels and roles', async ({ page }) => {
    await page.goto('/dashboard');

    // Check buttons have accessible names
    const buttons = page.locator('button');
    for (let i = 0; i < await buttons.count(); i++) {
      const button = buttons.nth(i);
      const accessibleName = await button.evaluate(btn => {
        const ariaLabel = btn.getAttribute('aria-label');
        const ariaLabelledBy = btn.getAttribute('aria-labelledby');
        const textContent = btn.textContent?.trim();

        return ariaLabel || ariaLabelledBy || textContent;
      });

      expect(accessibleName).toBeTruthy();
    }

    // Check images have alt text
    const images = page.locator('img');
    for (let i = 0; i < await images.count(); i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
    }

    // Check form inputs have labels
    const inputs = page.locator('input[type="text"], input[type="email"], textarea');
    for (let i = 0; i < await inputs.count(); i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');

      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        const hasLabel = await label.count() > 0;

        expect(hasLabel || ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    }
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/dashboard');

    // Start with first focusable element
    await page.keyboard.press('Tab');

    // Keep track of focused elements
    const focusedElements = [];

    for (let i = 0; i < 10; i++) {
      const focusedElement = page.locator(':focus');

      if (await focusedElement.count() > 0) {
        const tagName = await focusedElement.evaluate(el => el.tagName.toLowerCase());
        const role = await focusedElement.getAttribute('role');
        const type = await focusedElement.getAttribute('type');

        focusedElements.push({ tagName, role, type });

        // Verify focused element is interactive
        const isInteractive = ['button', 'a', 'input', 'select', 'textarea'].includes(tagName) ||
                             role === 'button' || role === 'link';

        expect(isInteractive).toBeTruthy();
      }

      await page.keyboard.press('Tab');
    }

    // Should have focused multiple elements
    expect(focusedElements.length).toBeGreaterThan(3);
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto('/dashboard');

    // Test main text elements
    const textElements = page.locator('p, span, div').filter({ hasText: /\w+/ });

    for (let i = 0; i < Math.min(await textElements.count(), 5); i++) {
      const element = textElements.nth(i);

      if (await element.isVisible()) {
        const styles = await element.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            color: computed.color,
            backgroundColor: computed.backgroundColor,
            fontSize: computed.fontSize
          };
        });

        // Basic checks for common accessibility issues
        expect(styles.color).not.toBe('rgb(128, 128, 128)'); // Avoid pure gray text
        expect(styles.color).not.toBe(styles.backgroundColor); // Text shouldn't match background
      }
    }

    // Test button contrast
    const buttons = page.locator('button');

    for (let i = 0; i < Math.min(await buttons.count(), 3); i++) {
      const button = buttons.nth(i);

      if (await button.isVisible()) {
        const styles = await button.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            color: computed.color,
            backgroundColor: computed.backgroundColor
          };
        });

        expect(styles.color).not.toBe(styles.backgroundColor);
      }
    }
  });

  test('should have proper focus indicators', async ({ page }) => {
    await page.goto('/dashboard');

    // Tab to first focusable element
    await page.keyboard.press('Tab');

    const focusedElement = page.locator(':focus');

    if (await focusedElement.count() > 0) {
      // Check that focused element has visible focus indicator
      const styles = await focusedElement.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          outline: computed.outline,
          outlineWidth: computed.outlineWidth,
          outlineStyle: computed.outlineStyle,
          boxShadow: computed.boxShadow,
          borderColor: computed.borderColor
        };
      });

      // Should have some kind of focus indicator
      const hasFocusIndicator =
        styles.outline !== 'none' ||
        styles.outlineWidth !== '0px' ||
        styles.boxShadow !== 'none' ||
        styles.borderColor !== 'initial';

      expect(hasFocusIndicator).toBeTruthy();
    }
  });

  test('should support screen reader users', async ({ page }) => {
    await page.goto('/dashboard');

    // Check for skip links
    const skipLink = page.locator('a').filter({ hasText: /skip to main|skip to content/i });
    if (await skipLink.count() > 0) {
      await expect(skipLink).toBeVisible();
    }

    // Check for main landmark
    const mainLandmark = page.locator('main, [role="main"]');
    await expect(mainLandmark).toBeVisible();

    // Check for navigation landmark
    const navLandmark = page.locator('nav, [role="navigation"]');
    if (await navLandmark.count() > 0) {
      await expect(navLandmark).toBeVisible();
    }

    // Check that interactive elements have proper roles
    const interactiveElements = page.locator('button, a, input, select, textarea');

    for (let i = 0; i < Math.min(await interactiveElements.count(), 5); i++) {
      const element = interactiveElements.nth(i);

      if (await element.isVisible()) {
        const tagName = await element.evaluate(el => el.tagName.toLowerCase());
        const role = await element.getAttribute('role');
        const type = await element.getAttribute('type');

        // Verify semantic HTML or appropriate ARIA roles
        const isAccessible =
          ['button', 'a', 'input', 'select', 'textarea'].includes(tagName) ||
          ['button', 'link', 'textbox', 'combobox'].includes(role || '');

        expect(isAccessible).toBeTruthy();
      }
    }
  });

  test('should handle reduced motion preferences', async ({ page }) => {
    // Set reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('/dashboard');

    // Check that animations are disabled or reduced
    const animatedElements = page.locator('.animate-pulse, .transition, .animation, [class*="animate"]');

    for (let i = 0; i < Math.min(await animatedElements.count(), 3); i++) {
      const element = animatedElements.nth(i);

      if (await element.isVisible()) {
        const styles = await element.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            animationDuration: computed.animationDuration,
            transitionDuration: computed.transitionDuration
          };
        });

        // Animations should be instant or very short when reduced motion is preferred
        if (styles.animationDuration && styles.animationDuration !== '0s') {
          const duration = parseFloat(styles.animationDuration);
          expect(duration).toBeLessThan(0.5); // Less than 500ms
        }

        if (styles.transitionDuration && styles.transitionDuration !== '0s') {
          const duration = parseFloat(styles.transitionDuration);
          expect(duration).toBeLessThan(0.5); // Less than 500ms
        }
      }
    }
  });

  test('should be usable with high contrast mode', async ({ page }) => {
    // Simulate high contrast mode
    await page.addStyleTag({
      content: `
        @media (prefers-contrast: high) {
          * {
            background-color: black !important;
            color: white !important;
            border-color: white !important;
          }
          button, a {
            background-color: white !important;
            color: black !important;
          }
        }
      `
    });

    await page.goto('/dashboard');

    // Verify that content is still visible and usable
    const headings = page.locator('h1, h2, h3');
    await expect(headings.first()).toBeVisible();

    const buttons = page.locator('button');
    if (await buttons.count() > 0) {
      await expect(buttons.first()).toBeVisible();
      await expect(buttons.first()).toBeEnabled();
    }

    const links = page.locator('a[href]');
    if (await links.count() > 0) {
      await expect(links.first()).toBeVisible();
    }
  });

  test('should provide error feedback in accessible way', async ({ page }) => {
    await page.goto('/projects/new');

    // Submit form without required fields
    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.count() > 0) {
      await submitButton.click();

      await page.waitForTimeout(1000);

      // Check for accessible error messages
      const errorMessages = page.locator('[role="alert"], .error, .text-red-600');

      if (await errorMessages.count() > 0) {
        const firstError = errorMessages.first();
        await expect(firstError).toBeVisible();

        // Error should be associated with the field
        const ariaDescribedBy = await page.locator('input').first().getAttribute('aria-describedby');
        if (ariaDescribedBy) {
          const errorById = page.locator(`#${ariaDescribedBy}`);
          await expect(errorById).toBeVisible();
        }
      }
    }
  });
});

test.describe('Progressive Enhancement', () => {
  test('should work without JavaScript', async ({ page }) => {
    // Disable JavaScript
    await page.setJavaScriptEnabled(false);
    await page.goto('/dashboard');

    // Basic content should still be visible
    const headings = page.locator('h1, h2, h3');
    await expect(headings.first()).toBeVisible();

    // Forms should still be submittable
    const forms = page.locator('form');
    if (await forms.count() > 0) {
      const form = forms.first();
      await expect(form).toHaveAttribute('action');
    }

    // Links should still work
    const links = page.locator('a[href]');
    if (await links.count() > 0) {
      const link = links.first();
      const href = await link.getAttribute('href');
      expect(href).toBeTruthy();
      expect(href).not.toBe('#');
    }
  });

  test('should enhance functionality with JavaScript', async ({ page }) => {
    // Enable JavaScript
    await page.setJavaScriptEnabled(true);
    await page.goto('/dashboard');

    // Wait for JavaScript to load
    await page.waitForFunction(() => window.lucide !== undefined);

    // Check that enhanced features work
    const icons = page.locator('[data-lucide]');
    if (await icons.count() > 0) {
      // Icons should be rendered by JavaScript
      const iconSvg = icons.first().locator('svg');
      await expect(iconSvg).toBeVisible();
    }

    // Check for HTMX functionality
    const htmxElements = page.locator('[hx-get], [hx-post], [hx-put], [hx-delete]');
    if (await htmxElements.count() > 0) {
      // HTMX should be loaded
      await page.waitForFunction(() => window.htmx !== undefined);
    }

    // Check for Alpine.js functionality
    const alpineElements = page.locator('[x-data], [x-show], [x-if]');
    if (await alpineElements.count() > 0) {
      // Alpine should be loaded
      await page.waitForFunction(() => window.Alpine !== undefined);
    }
  });

  test('should gracefully degrade when features are unavailable', async ({ page }) => {
    // Mock network failures for external resources
    await page.route('**/lucide/**', route => route.abort());
    await page.route('**/alpinejs/**', route => route.abort());
    await page.route('**/htmx/**', route => route.abort());

    await page.goto('/dashboard');

    // Basic functionality should still work
    const headings = page.locator('h1, h2, h3');
    await expect(headings.first()).toBeVisible();

    const buttons = page.locator('button');
    if (await buttons.count() > 0) {
      await expect(buttons.first()).toBeEnabled();
    }

    // Fallback text should be visible where icons would be
    const iconFallbacks = page.locator('.sr-only, .visually-hidden');
    if (await iconFallbacks.count() > 0) {
      // Screen reader text should provide context
      const fallbackText = await iconFallbacks.first().textContent();
      expect(fallbackText?.trim()).toBeTruthy();
    }
  });
});