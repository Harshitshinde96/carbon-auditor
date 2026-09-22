'use client';

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export interface ScopeChartProps {
  data: Array<{
    name: string;
    scope1: number;
    scope2: number;
    scope3: number;
  }>;
}

export function ScopeChart({ data }: ScopeChartProps) {
  return (
    <div className="h-[400px] w-full" data-testid="scope-chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <defs>
            {/* Pattern for Scope 1: Stripes */}
            <pattern id="pattern-scope1" patternUnits="userSpaceOnUse" width="4" height="4">
              <path d="M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2" stroke="#000" strokeWidth="1" />
            </pattern>
            {/* Pattern for Scope 2: Dots */}
            <pattern id="pattern-scope2" patternUnits="userSpaceOnUse" width="4" height="4">
              <circle cx="2" cy="2" r="1.5" fill="#555" />
            </pattern>
            {/* Pattern for Scope 3: Crosshatch */}
            <pattern id="pattern-scope3" patternUnits="userSpaceOnUse" width="8" height="8">
              <path d="M0 0L8 8ZM8 0L0 8Z" stroke="#888" strokeWidth="1" />
            </pattern>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} tickFormatter={(value) => `${value}kg`} />
          <Tooltip 
            cursor={{ fill: 'rgba(0,0,0,0.05)' }} 
            contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', borderRadius: '6px' }}
          />
          <Legend />
          <Bar dataKey="scope1" name="Scope 1" stackId="a" fill="url(#pattern-scope1)" stroke="#000" />
          <Bar dataKey="scope2" name="Scope 2" stackId="a" fill="url(#pattern-scope2)" stroke="#555" />
          <Bar dataKey="scope3" name="Scope 3" stackId="a" fill="url(#pattern-scope3)" stroke="#888" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
