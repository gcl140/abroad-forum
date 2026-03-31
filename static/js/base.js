// Toast auto-dismiss
document.addEventListener("DOMContentLoaded", function () {
    const toastMessages = document.querySelectorAll('.animate-fade-in-up');

    toastMessages.forEach(toast => {
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 10000);

        toast.addEventListener('mouseenter', () => {
            const progressBar = toast.querySelector('.animate-progress');
            progressBar.style.animationPlayState = 'paused';
        });

        toast.addEventListener('mouseleave', () => {
            const progressBar = toast.querySelector('.animate-progress');
            progressBar.style.animationPlayState = 'running';
        });
    });
});

// Mobile sidebar toggle
const sidebarToggle = document.getElementById("sidebarToggle");
const mobileSidebar = document.getElementById("mobileSidebar");
const mobileSidebarClose = document.getElementById("mobileSidebarClose");

function closeMobileSidebar() {
    mobileSidebar.classList.add("hidden");
}

sidebarToggle.addEventListener("click", () => {
    mobileSidebar.classList.remove("hidden");
});

if (mobileSidebarClose) {
    mobileSidebarClose.addEventListener("click", closeMobileSidebar);
}

document.addEventListener("click", (e) => {
    if (!mobileSidebar.contains(e.target) && !sidebarToggle.contains(e.target) && !mobileSidebar.classList.contains("hidden")) {
        closeMobileSidebar();
    }
});

// Desktop sidebar collapse/expand (icon-only mode)
const desktopSidebar = document.getElementById("mobileSidebar");
const collapseBtn = document.getElementById("sidebarCollapseBtn");
let sidebarCollapsed = localStorage.getItem("fa-sidebar") === "closed";

function setSidebarCollapsed(collapsed) {
    if (window.innerWidth < 1024) return;
    desktopSidebar.setAttribute("data-collapsed", collapsed ? "true" : "false");
    desktopSidebar.style.width = collapsed ? "4rem" : "";
    desktopSidebar.style.overflow = collapsed ? "visible" : "";

    desktopSidebar.querySelectorAll(".sidebar-text").forEach(el => {
        el.style.display = collapsed ? "none" : "";
    });
    desktopSidebar.querySelectorAll(".sidebar-extra").forEach(el => {
        el.style.display = collapsed ? "none" : "";
    });

    const nav = document.getElementById("sidebarNav");
    if (nav) {
        nav.style.display = collapsed ? "flex" : "";
        nav.style.flexDirection = collapsed ? "column" : "";
        nav.style.alignItems = collapsed ? "center" : "";
        nav.style.gap = collapsed ? "0.75rem" : "";
    }

    desktopSidebar.querySelectorAll(".sidebar-link").forEach(el => {
        el.style.justifyContent = collapsed ? "center" : "";
        el.style.gap = collapsed ? "0" : "";
        el.style.padding = collapsed ? "0.6rem" : "";
        el.style.width = collapsed ? "2.5rem" : "";
        el.style.borderRadius = collapsed ? "0.5rem" : "";
    });

    const logo = document.getElementById("sidebarLogo");
    if (logo) logo.style.display = collapsed ? "none" : "";

    const collapseWrapper = document.querySelector("#mobileSidebar .flex.items-center.justify-between");
    if (collapseWrapper) collapseWrapper.style.justifyContent = collapsed ? "center" : "";

    const icon = document.getElementById("collapseIcon");
    if (icon) icon.className = collapsed ? "fas fa-chevron-right text-sm" : "fas fa-chevron-left text-sm";
}

setSidebarCollapsed(sidebarCollapsed);

collapseBtn && collapseBtn.addEventListener("click", () => {
    sidebarCollapsed = !sidebarCollapsed;
    localStorage.setItem("fa-sidebar", sidebarCollapsed ? "closed" : "open");
    setSidebarCollapsed(sidebarCollapsed);
});

// Theme toggle
function applyTheme(t) {
    document.documentElement.setAttribute("data-theme", t);
    const isLight = t === "light";
    // Dropdown icon
    const icon = document.getElementById("theme-icon");
    const label = document.getElementById("theme-label");
    if (icon) icon.className = isLight ? "fas fa-moon w-4" : "fas fa-sun w-4";
    if (label) label.textContent = isLight ? "Dark mode" : "Light mode";
    // Profile header icon
    const profileIcon = document.getElementById("theme-icon-profile");
    if (profileIcon) profileIcon.className = isLight ? "fas fa-moon" : "fas fa-sun";
}
window.toggleTheme = function () {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "light" ? "dark" : "light";
    localStorage.setItem("fa-theme", next);
    applyTheme(next);
};
applyTheme(localStorage.getItem("fa-theme") || "light");

// Back to Top Button
const backToTopButton = document.getElementById('back-to-top');

window.addEventListener('scroll', () => {
    if (window.pageYOffset > 300) {
        backToTopButton.classList.remove('opacity-0', 'invisible');
        backToTopButton.classList.add('opacity-100', 'visible');
    } else {
        backToTopButton.classList.add('opacity-0', 'invisible');
        backToTopButton.classList.remove('opacity-100', 'visible');
    }
});

backToTopButton.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Alpine.js dropdown init
document.addEventListener('alpine:init', () => {
    Alpine.data('dropdown', () => ({
        open: false,
        toggle() {
            this.open = !this.open;
        }
    }));
});

// Preloader
window.addEventListener("load", function () {
    const preloader = document.getElementById("preloader");
    if (preloader) {
        preloader.style.opacity = "0";
        setTimeout(() => {
            preloader.style.display = "none";
            document.body.classList.remove("loading");
        }, 500);
    }
});
