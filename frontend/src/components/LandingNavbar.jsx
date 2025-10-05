import React, { useState } from 'react';
import {
  Navbar,
  NavBody,
  NavItems,
  MobileNav,
  MobileNavHeader,
  MobileNavMenu,
  MobileNavToggle,
  NavbarLogo,
  NavbarButton,
} from './ui/resizable-navbar';

const LandingNavbar = ({ onStartLiveCall }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { name: 'Home', link: '#home' },
    { name: 'About', link: '#data' },
    { name: 'Services', link: '#features' },
  ];

  const handleItemClick = () => {
    setIsMobileMenuOpen(false);
  };

  const handleSmoothScroll = (e, targetId) => {
    e.preventDefault();
    const element = document.getElementById(targetId);
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }
    setIsMobileMenuOpen(false);
  };

  const handleStartLiveCall = () => {
    if (onStartLiveCall) {
      onStartLiveCall();
    }
    setIsMobileMenuOpen(false);
  };

  return (
    <Navbar>
      <NavBody>
        <NavbarLogo />
        <NavItems 
          items={navItems.map(item => ({
            ...item,
            onClick: (e) => {
              if (item.name === 'Home') {
                window.scrollTo({ top: 0, behavior: 'smooth' });
              } else {
                const targetId = item.link.replace('#', '');
                handleSmoothScroll(e, targetId);
              }
            }
          }))} 
          onItemClick={handleItemClick} 
        />
        <NavbarButton
          onClick={handleStartLiveCall}
          variant="primary"
          className="flex items-center space-x-2"
        >
          <span>📞</span>
          <span>Start Live Call</span>
        </NavbarButton>
      </NavBody>

      <MobileNav>
        <MobileNavHeader>
          <NavbarLogo />
          <MobileNavToggle
            isOpen={isMobileMenuOpen}
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          />
        </MobileNavHeader>
        <MobileNavMenu
          isOpen={isMobileMenuOpen}
          onClose={() => setIsMobileMenuOpen(false)}
        >
          {navItems.map((item, index) => (
            <button
              key={index}
              onClick={(e) => {
                if (item.name === 'Home') {
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                } else {
                  const targetId = item.link.replace('#', '');
                  handleSmoothScroll(e, targetId);
                }
              }}
              className="text-gray-700 hover:text-blue-600 block py-2 text-lg font-medium transition-colors w-full text-left"
            >
              {item.name}
            </button>
          ))}
          <NavbarButton
            onClick={handleStartLiveCall}
            variant="primary"
            className="mt-4 w-full flex items-center justify-center space-x-2"
          >
            <span>📞</span>
            <span>Start Live Call</span>
          </NavbarButton>
        </MobileNavMenu>
      </MobileNav>
    </Navbar>
  );
};

export default LandingNavbar;
