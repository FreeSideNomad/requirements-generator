// Navigation and Role-Based Hierarchy Management
class NavigationManager {
    constructor() {
        this.currentUser = null;
        this.sidebarElement = null;
        this.mobileMenuOpen = false;
        this.init();
    }

    init() {
        this.sidebarElement = document.getElementById('sidebar');
        this.setupEventListeners();
        this.setupHtmxEvents();
        this.loadUserPermissions();
    }

    setupEventListeners() {
        // Mobile menu toggle
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => this.toggleMobileMenu());
        }

        // Sidebar collapse/expand
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (this.mobileMenuOpen && !this.sidebarElement?.contains(e.target) &&
                !e.target.closest('#mobile-menu-btn')) {
                this.closeMobileMenu();
            }
        });

        // Handle ESC key to close mobile menu
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.mobileMenuOpen) {
                this.closeMobileMenu();
            }
        });
    }

    setupHtmxEvents() {
        // Update navigation after HTMX requests
        document.body.addEventListener('htmx:afterRequest', (event) => {
            if (event.detail.xhr.status === 401) {
                // Handle unauthorized access
                this.handleUnauthorized();
            }
        });

        // Update active nav item after page changes
        document.body.addEventListener('htmx:afterSettle', () => {
            this.updateActiveNavItem();
        });
    }

    toggleMobileMenu() {
        this.mobileMenuOpen = !this.mobileMenuOpen;
        if (this.sidebarElement) {
            this.sidebarElement.classList.toggle('open', this.mobileMenuOpen);
        }

        // Update aria attributes for accessibility
        const menuBtn = document.getElementById('mobile-menu-btn');
        if (menuBtn) {
            menuBtn.setAttribute('aria-expanded', this.mobileMenuOpen.toString());
        }
    }

    closeMobileMenu() {
        this.mobileMenuOpen = false;
        if (this.sidebarElement) {
            this.sidebarElement.classList.remove('open');
        }

        const menuBtn = document.getElementById('mobile-menu-btn');
        if (menuBtn) {
            menuBtn.setAttribute('aria-expanded', 'false');
        }
    }

    toggleSidebar() {
        const mainContent = document.getElementById('main-content');
        const isCollapsed = this.sidebarElement?.classList.contains('collapsed');

        if (this.sidebarElement) {
            this.sidebarElement.classList.toggle('collapsed');
        }

        if (mainContent) {
            mainContent.classList.toggle('sidebar-collapsed');
        }

        // Store preference
        localStorage.setItem('sidebar-collapsed', (!isCollapsed).toString());
    }

    updateActiveNavItem() {
        const currentPath = window.location.pathname;

        // Remove active class from all nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });

        // Add active class to current nav item
        const activeItem = document.querySelector(`[data-nav-path="${currentPath}"]`);
        if (activeItem) {
            activeItem.classList.add('active');

            // Expand parent groups if necessary
            const parentGroup = activeItem.closest('.nav-group');
            if (parentGroup) {
                const toggle = parentGroup.querySelector('.nav-group-toggle');
                if (toggle && !parentGroup.classList.contains('expanded')) {
                    this.toggleNavGroup(toggle);
                }
            }
        }
    }

    toggleNavGroup(toggleElement) {
        const group = toggleElement.closest('.nav-group');
        const content = group.querySelector('.nav-group-content');
        const icon = toggleElement.querySelector('.nav-group-icon');

        if (group.classList.contains('expanded')) {
            // Collapse
            group.classList.remove('expanded');
            content.style.maxHeight = '0';
            icon.style.transform = 'rotate(0deg)';
        } else {
            // Expand
            group.classList.add('expanded');
            content.style.maxHeight = content.scrollHeight + 'px';
            icon.style.transform = 'rotate(90deg)';
        }

        // Store preference
        const groupId = group.getAttribute('data-group-id');
        if (groupId) {
            const expandedGroups = JSON.parse(localStorage.getItem('expanded-nav-groups') || '[]');
            if (group.classList.contains('expanded')) {
                if (!expandedGroups.includes(groupId)) {
                    expandedGroups.push(groupId);
                }
            } else {
                const index = expandedGroups.indexOf(groupId);
                if (index > -1) {
                    expandedGroups.splice(index, 1);
                }
            }
            localStorage.setItem('expanded-nav-groups', JSON.stringify(expandedGroups));
        }
    }

    loadUserPermissions() {
        // This would typically fetch from the server
        fetch('/api/auth/permissions')
            .then(response => response.json())
            .then(data => {
                this.currentUser = data;
                this.updateNavigationVisibility();
            })
            .catch(error => {
                console.error('Failed to load user permissions:', error);
            });
    }

    updateNavigationVisibility() {
        if (!this.currentUser) return;

        const { role, permissions } = this.currentUser;

        // Hide/show navigation items based on role and permissions
        document.querySelectorAll('[data-required-role]').forEach(element => {
            const requiredRole = element.getAttribute('data-required-role');
            const hasRole = this.hasRole(role, requiredRole);
            element.style.display = hasRole ? 'block' : 'none';
        });

        document.querySelectorAll('[data-required-permission]').forEach(element => {
            const requiredPermission = element.getAttribute('data-required-permission');
            const hasPermission = permissions.includes(requiredPermission);
            element.style.display = hasPermission ? 'block' : 'none';
        });

        // Update tenant-specific navigation
        this.updateTenantNavigation();
    }

    hasRole(userRole, requiredRole) {
        const roleHierarchy = {
            'super_admin': 4,
            'tenant_admin': 3,
            'team_lead': 2,
            'contributor': 1,
            'reader': 0
        };

        return roleHierarchy[userRole] >= roleHierarchy[requiredRole];
    }

    updateTenantNavigation() {
        const tenantContext = this.currentUser.current_tenant;
        if (tenantContext) {
            // Update tenant-specific styling
            document.documentElement.setAttribute('data-tenant', tenantContext.industry);

            // Update tenant name in navigation
            const tenantNameElement = document.getElementById('current-tenant-name');
            if (tenantNameElement) {
                tenantNameElement.textContent = tenantContext.name;
            }

            // Show/hide tenant-specific features
            document.querySelectorAll('[data-tenant-feature]').forEach(element => {
                const feature = element.getAttribute('data-tenant-feature');
                const hasFeature = tenantContext.features?.includes(feature);
                element.style.display = hasFeature ? 'block' : 'none';
            });
        }
    }

    handleUnauthorized() {
        // Redirect to login or show unauthorized message
        window.location.href = '/auth/login';
    }

    // Restore navigation state from localStorage
    restoreNavigationState() {
        // Restore sidebar collapsed state
        const sidebarCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
        if (sidebarCollapsed && this.sidebarElement) {
            this.sidebarElement.classList.add('collapsed');
            const mainContent = document.getElementById('main-content');
            if (mainContent) {
                mainContent.classList.add('sidebar-collapsed');
            }
        }

        // Restore expanded nav groups
        const expandedGroups = JSON.parse(localStorage.getItem('expanded-nav-groups') || '[]');
        expandedGroups.forEach(groupId => {
            const group = document.querySelector(`[data-group-id="${groupId}"]`);
            if (group) {
                const toggle = group.querySelector('.nav-group-toggle');
                if (toggle) {
                    this.toggleNavGroup(toggle);
                }
            }
        });
    }
}

// Alpine.js data for reactive navigation components
function navigationData() {
    return {
        mobileMenuOpen: false,
        currentPath: window.location.pathname,

        toggleMobileMenu() {
            this.mobileMenuOpen = !this.mobileMenuOpen;
        },

        closeMobileMenu() {
            this.mobileMenuOpen = false;
        },

        isActivePath(path) {
            return this.currentPath.startsWith(path);
        }
    };
}

// Initialize navigation when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const nav = new NavigationManager();
    nav.restoreNavigationState();

    // Make navigation manager available globally for HTMX interactions
    window.navigationManager = nav;
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NavigationManager, navigationData };
}