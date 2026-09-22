'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowRight, Calendar, Mic, Search, MoreVertical, Settings2, Filter, Lock } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['emissions-summary'],
    queryFn: async () => {
      const response = await apiClient('/emissions/summary');
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-48 rounded-[2rem]" />
          <Skeleton className="h-48 rounded-[2rem]" />
          <Skeleton className="h-48 rounded-[2rem]" />
        </div>
        <Skeleton className="h-[400px] rounded-[2rem]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 border border-ink bg-surface/10 rounded-[2rem]">
        <p className="text-ink font-semibold">Failed to load dashboard data</p>
      </div>
    );
  }

  const date = new Date();
  const day = date.getDate();
  const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
  const monthName = date.toLocaleDateString('en-US', { month: 'long' });

  const totalEmissions = summary?.total_co2e_kg || 0;
  const scope1 = summary?.breakdown?.['SCOPE_1'] || 0;
  const scope2 = summary?.breakdown?.['SCOPE_2'] || 0;
  const scope3 = summary?.breakdown?.['SCOPE_3'] || 0;
  
  const scope3Percent = totalEmissions > 0 ? Math.round((scope3 / totalEmissions) * 100) : 0;

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      
      {/* Top Banner Row */}
      <div className="flex flex-col lg:flex-row gap-8 items-center justify-between">
        
        {/* Date & Action */}
        <div className="flex items-center gap-6">
          <div className="w-20 h-20 rounded-full border border-border/50 flex items-center justify-center bg-background shadow-sm">
            <span className="text-2xl font-bold">{day}</span>
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-lg">{dayName},</span>
            <span className="text-muted">{monthName}</span>
          </div>
          <Link href="/upload">
            <button className="ml-4 bg-accent hover:bg-accent-hover text-surface px-6 py-4 rounded-full flex items-center gap-4 transition-colors shadow-md shadow-accent/20">
              <span className="font-medium">Upload a Bill</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </Link>
          <div className="w-12 h-12 rounded-full border border-border/50 flex items-center justify-center bg-background text-accent relative">
            <Calendar className="w-5 h-5" />
            <div className="absolute top-3 right-3 w-2 h-2 bg-accent rounded-full border-2 border-background"></div>
          </div>
        </div>

        {/* AI Greeting */}
        <div className="flex items-center gap-6 pr-8">
          <div className="flex flex-col items-end">
            <h2 className="text-2xl font-semibold">Hey, Need help? 👋</h2>
            <h2 className="text-2xl text-muted">Just ask me anything!</h2>
          </div>
          <Link href="/chat">
            <div className="w-16 h-16 rounded-full border border-border/50 bg-background flex items-center justify-center shadow-sm hover:bg-border/50 cursor-pointer transition-colors">
              <Mic className="w-6 h-6 text-ink" />
            </div>
          </Link>
        </div>

      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Total CO2e - Black Card */}
        <div className="lg:col-span-4 bg-ink text-surface rounded-[2.5rem] p-8 flex flex-col justify-between shadow-xl relative overflow-hidden">
          <div className="flex justify-between items-center mb-8">
            <span className="font-bold tracking-widest text-lg">TOTAL CO2e</span>
            <div className="bg-surface text-ink text-xs font-semibold px-4 py-2 rounded-full">
              Current Period
            </div>
          </div>
          <div className="flex flex-col gap-2 mb-8">
            <span className="text-muted text-sm">Carbon Footprint</span>
            <span className="text-3xl font-mono tracking-wider">
              {totalEmissions > 0 ? `${totalEmissions.toLocaleString()} kg` : '**** 0000'}
            </span>
          </div>
          <div className="flex gap-4">
            <button className="flex-1 bg-surface text-ink font-semibold py-3 rounded-full hover:bg-surface-muted transition-colors">
              Details
            </button>
            <Link href="/reports" className="flex-1">
              <button className="w-full bg-surface/20 text-surface font-semibold py-3 rounded-full hover:bg-surface/30 transition-colors">
                Report
              </button>
            </Link>
          </div>
        </div>

        {/* Scope 1 & 2 Cards */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          {/* Scope 1 */}
          <div className="bg-background rounded-[2rem] p-6 flex flex-col justify-between flex-1 border border-border/40">
            <div className="flex justify-between items-center mb-4">
              <div className="w-10 h-10 rounded-full border border-border flex items-center justify-center bg-surface">
                <span className="text-xs font-bold">S1</span>
              </div>
              <div className="bg-surface border border-border/50 text-xs px-3 py-1.5 rounded-full flex items-center gap-1">
                Direct
                <ArrowRight className="w-3 h-3 rotate-45" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-muted text-sm mb-1">Scope 1 Emissions</span>
              <span className="text-2xl font-bold">{scope1 > 0 ? scope1.toLocaleString() : '0'} <span className="text-sm font-normal text-muted">kg</span></span>
            </div>
          </div>

          {/* Scope 2 */}
          <div className="bg-background rounded-[2rem] p-6 flex flex-col justify-between flex-1 border border-border/40">
            <div className="flex justify-between items-center mb-4">
              <div className="w-10 h-10 rounded-full border border-border flex items-center justify-center bg-surface">
                <span className="text-xs font-bold">S2</span>
              </div>
              <div className="bg-surface border border-border/50 text-xs px-3 py-1.5 rounded-full flex items-center gap-1">
                Indirect
                <ArrowRight className="w-3 h-3 rotate-45" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-muted text-sm mb-1">Scope 2 Emissions</span>
              <span className="text-2xl font-bold">{scope2 > 0 ? scope2.toLocaleString() : '0'} <span className="text-sm font-normal text-muted">kg</span></span>
            </div>
          </div>
        </div>

        {/* Scope 3 Donut / Stats */}
        <div className="lg:col-span-2 flex flex-col gap-4 items-center">
          <div className="bg-background rounded-full w-32 h-32 flex flex-col items-center justify-center border border-border/40 shadow-sm mt-4">
            <Lock className="w-5 h-5 mb-1" />
            <span className="text-xs font-semibold text-center">Value<br/>Chain</span>
          </div>
          <div className="mt-4 relative w-32 h-32 rounded-full border-8 border-background bg-ink flex flex-col items-center justify-center text-surface shadow-md">
            <span className="text-xl font-bold">{scope3Percent}%</span>
            <span className="text-[10px] text-muted">Scope 3</span>
            {/* Pseudo-element for the colored ring would go here in a real implementation */}
            <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="46" fill="none" stroke="#ED5B46" strokeWidth="8" strokeDasharray={`${scope3Percent * 2.89} 289`} className="transition-all duration-1000 ease-out" />
            </svg>
          </div>
        </div>

        {/* Small Metric Card */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="bg-background rounded-[2rem] p-6 flex flex-col border border-border/40 h-full">
            <div className="flex justify-between items-center mb-6">
               <div className="w-8 h-8 rounded-full border border-border flex items-center justify-center bg-surface">
                  <span className="w-2 h-2 bg-ink rounded-full"></span>
               </div>
            </div>
            <span className="text-2xl font-bold">12 <span className="text-lg font-normal">Bills</span></span>
            <span className="text-xs text-muted mb-4">Processed this year</span>
            <div className="flex gap-1 mt-auto">
               {[...Array(12)].map((_, i) => (
                 <div key={i} className={`w-3 h-3 rounded-full ${i < 8 ? 'bg-accent' : 'bg-border'}`}></div>
               ))}
            </div>
          </div>
        </div>

      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Breakdown - Concentric Circles */}
        <div className="lg:col-span-4 bg-background rounded-[2.5rem] p-8 border border-border/40 flex flex-col items-center relative overflow-hidden">
          <div className="w-full flex justify-between items-center z-10 mb-8">
            <span className="font-semibold">Emissions Breakdown</span>
            <div className="bg-surface border border-border text-xs px-3 py-1 rounded-full">
              Current Year
            </div>
          </div>
          
          <div className="relative w-64 h-64 flex items-center justify-center my-4">
            {/* Concentric Circles Visualization */}
            <div className="absolute w-64 h-64 rounded-full bg-chart-4 flex items-start justify-center pt-6 opacity-70">
              <span className="text-xs font-semibold text-accent">Total</span>
            </div>
            <div className="absolute w-48 h-48 rounded-full bg-chart-3 flex items-start justify-center pt-5 shadow-sm">
              <span className="text-xs font-semibold text-accent">Scope 3</span>
            </div>
            <div className="absolute w-32 h-32 rounded-full bg-chart-2 flex items-start justify-center pt-4 shadow-sm">
              <span className="text-xs font-semibold text-surface">Scope 2</span>
            </div>
            <div className="absolute w-16 h-16 rounded-full bg-chart-1 flex items-center justify-center shadow-md">
              <span className="text-xs font-semibold text-surface">S1</span>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="lg:col-span-8 bg-background rounded-[2.5rem] p-8 border border-border/40 flex flex-col">
          <div className="flex justify-between items-center mb-8">
            <span className="font-semibold">Activity manager</span>
            <div className="flex gap-2">
              <button className="w-10 h-10 rounded-full border border-border flex items-center justify-center hover:bg-surface transition-colors">
                 <MoreVertical className="w-4 h-4" />
              </button>
              <button className="w-10 h-10 rounded-full border border-border flex items-center justify-center hover:bg-surface transition-colors">
                 <Settings2 className="w-4 h-4" />
              </button>
              <button className="bg-surface border border-border px-4 py-2 rounded-full flex items-center gap-2 font-medium text-sm hover:bg-border/20 transition-colors">
                 <Filter className="w-4 h-4" />
                 Filters
              </button>
            </div>
          </div>
          
          <div className="flex items-center gap-4 mb-8">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-muted absolute left-4 top-1/2 -translate-y-1/2" />
              <input 
                type="text" 
                placeholder="Search in activities..." 
                className="w-full pl-12 pr-4 py-3 bg-surface border-none rounded-full text-sm focus:outline-none focus:ring-1 focus:ring-border placeholder:text-muted shadow-sm"
              />
            </div>
            <div className="flex gap-2">
              <div className="bg-surface border border-border px-4 py-2 rounded-full flex items-center gap-2 text-sm font-medium shadow-sm">
                Team <span className="w-2 h-2 bg-accent rounded-full"></span>
              </div>
              <div className="bg-surface border border-border px-4 py-2 rounded-full flex items-center gap-2 text-sm font-medium shadow-sm">
                Insights <span className="text-muted text-xs">×</span>
              </div>
            </div>
          </div>
          
          <div className="flex-1 flex items-center justify-center border-t border-border/50 pt-8 mt-auto">
             <Link href="/bills" className="text-ink font-medium hover:underline">View all processed bills</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
