'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, Plus, Share2, Search, LayoutDashboard, FileUp, Receipt, FileText, MessageSquare, Settings } from 'lucide-react';

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const pathname = usePathname();

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/upload', label: 'Upload', icon: FileUp },
    { href: '/bills', label: 'Bills', icon: Receipt },
    { href: '/reports', label: 'Reports', icon: FileText },
    { href: '/chat', label: 'Chat', icon: MessageSquare },
    { href: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-background p-4 md:p-6 overflow-hidden">
      {/* Main App Card - Highly Rounded */}
      <div className="flex-1 flex overflow-hidden bg-surface rounded-[2.5rem] shadow-soft border border-border/50 relative">
        
        {/* Collapsible Sidebar */}
        <aside className={`${isSidebarOpen ? 'w-64' : 'w-24'} transition-all duration-300 ease-in-out border-r border-border/40 flex flex-col items-center py-8 z-10 bg-surface`}>
          <button 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 mb-8 hover:bg-background rounded-xl transition-colors"
          >
            <Menu className="w-6 h-6 text-ink" />
          </button>

          <div className="w-12 h-12 bg-ink rounded-full flex items-center justify-center text-surface font-bold text-xl mb-12 flex-shrink-0">
            Nº
          </div>

          <nav className="flex-1 flex flex-col gap-4 w-full px-4">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link 
                  key={item.href} 
                  href={item.href}
                  className={`flex items-center p-3 rounded-2xl transition-colors ${isActive ? 'bg-accent text-surface' : 'text-ink-secondary hover:bg-background hover:text-ink'}`}
                  title={item.label}
                >
                  <item.icon className={`w-6 h-6 flex-shrink-0 ${isSidebarOpen ? 'mr-4' : 'mx-auto'}`} />
                  {isSidebarOpen && <span className="font-medium whitespace-nowrap">{item.label}</span>}
                </Link>
              );
            })}
          </nav>

          <div className="flex flex-col gap-4 mt-auto">
            <button className="w-12 h-12 bg-background border border-border/50 rounded-full flex items-center justify-center hover:bg-border/50 transition-colors flex-shrink-0">
              <Plus className="w-5 h-5 text-ink-secondary" />
            </button>
            <button className="w-12 h-12 bg-background border border-border/50 rounded-full flex items-center justify-center hover:bg-border/50 transition-colors flex-shrink-0">
              <Share2 className="w-5 h-5 text-ink-secondary" />
            </button>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <header className="h-24 flex items-center px-8 justify-between">
            <div className="flex flex-col">
              <h2 className="text-xl font-semibold text-ink leading-tight">Carbon Auditor</h2>
              <span className="text-muted text-sm">Dashboard</span>
            </div>
            
            <div className="flex items-center gap-6">
              <button className="w-10 h-10 bg-background border border-border/50 rounded-full flex items-center justify-center hover:bg-border/50 transition-colors">
                <Plus className="w-4 h-4 text-ink" />
              </button>
              
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-accent/20 rounded-full flex items-center justify-center overflow-hidden">
                   <div className="w-full h-full bg-accent/30 flex items-center justify-center text-accent font-bold">U</div>
                </div>
                <div className="flex flex-col hidden md:flex">
                  <span className="text-sm font-semibold text-ink leading-tight">Current User</span>
                  <span className="text-xs text-muted">Sustainability</span>
                </div>
              </div>

              <div className="relative hidden lg:block">
                <Search className="w-4 h-4 text-muted absolute left-4 top-1/2 -translate-y-1/2" />
                <input 
                  type="text" 
                  placeholder="Start searching here..." 
                  className="pl-12 pr-4 py-2 bg-background border-none rounded-full text-sm focus:outline-none focus:ring-1 focus:ring-border w-64 placeholder:text-muted"
                />
              </div>
            </div>
          </header>
          
          <main className="flex-1 overflow-y-auto px-8 pb-8">
            {children}
          </main>
        </div>

      </div>
    </div>
  );
}
