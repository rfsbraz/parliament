import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, Users, Building, Calendar, BarChart3, Menu, X, ChevronDown } from 'lucide-react';
import { useLegislatura } from '../contexts/LegislaturaContext';

// Navigation component with legislatura dropdown
const Navigation = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const location = useLocation();
  const { selectedLegislatura, legislaturas, selectLegislatura, loading } = useLegislatura();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/deputados', label: 'Deputados', icon: Users },
    { path: '/partidos', label: 'Partidos', icon: Building },
    { path: '/agenda', label: 'Agenda', icon: Calendar },
    { path: '/analises', label: 'Análises', icon: BarChart3 },
  ];

  const isActive = (path) => location.pathname === path;

  // Close dropdown when clicking outside  
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownOpen && !event.target.closest('.legislatura-dropdown')) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen]);

  return (
    <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center"
            >
              <Building className="w-5 h-5 text-white" />
            </motion.div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              Parlamento PT
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link key={item.path} to={item.path}>
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                      isActive(item.path)
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium">{item.label}</span>
                  </motion.div>
                </Link>
              );
            })}
          </div>

          {/* Legislatura Dropdown */}
          <div className="hidden md:flex items-center space-x-4">
            <div className="relative legislatura-dropdown">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                disabled={loading || !selectedLegislatura}
                className="flex items-center space-x-2 px-3 py-2 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <span className="text-sm font-medium text-gray-700">
                  {loading ? 'Carregando...' : selectedLegislatura?.designacao || 'Selecionar Legislatura'}
                </span>
                <ChevronDown className="w-4 h-4 text-gray-500" />
              </button>

              {dropdownOpen && !loading && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute right-0 mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
                >
                  <div className="py-1 max-h-64 overflow-y-auto">
                    {legislaturas.map((legislatura) => (
                      <button
                        key={legislatura.id}
                        onClick={() => {
                          selectLegislatura(legislatura);
                          setDropdownOpen(false);
                        }}
                        className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 transition-colors ${
                          selectedLegislatura?.id === legislatura.id
                            ? 'bg-blue-50 text-blue-700 font-medium'
                            : 'text-gray-700'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span>{legislatura.designacao}</span>
                          {legislatura.ativa && (
                            <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                              Ativa
                            </span>
                          )}
                        </div>
                        {legislatura.data_inicio && (
                          <div className="text-xs text-gray-500 mt-1">
                            {new Date(legislatura.data_inicio).getFullYear()}
                            {legislatura.data_fim && ` - ${new Date(legislatura.data_fim).getFullYear()}`}
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="md:hidden py-4 border-t border-gray-200"
          >
            <div className="space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsOpen(false)}
                    className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive(item.path)
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </motion.div>
        )}
      </div>
    </nav>
  );
};

export default Navigation;

