"use client";

import React, { useState, useMemo } from 'react';
import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react';
import { Pagination } from './Pagination';

export type SortDirection = 'asc' | 'desc' | null;

export interface Column<T> {
  key: string;
  title: React.ReactNode;
  sortable?: boolean;
  render?: (row: T) => React.ReactNode;
  // Optional custom sort function
  sortFn?: (a: T, b: T) => number;
}

export interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (row: T) => string | number;
  
  // Pagination
  pagination?: {
    page: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    disabled?: boolean;
  };
  
  // Empty state
  emptyState?: React.ReactNode;
}

export function DataTable<T>({ 
  data, 
  columns, 
  keyExtractor, 
  pagination,
  emptyState = <div className="p-8 text-center text-gray-500">No data available</div>
}: DataTableProps<T>) {
  
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDirection>(null);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      if (sortDir === 'asc') setSortDir('desc');
      else if (sortDir === 'desc') {
        setSortDir(null);
        setSortKey(null);
      }
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedData = useMemo(() => {
    if (!sortKey || !sortDir) return data;
    
    const column = columns.find(c => c.key === sortKey);
    if (!column) return data;

    return [...data].sort((a, b) => {
      let comparison = 0;
      
      if (column.sortFn) {
        comparison = column.sortFn(a, b);
      } else {
        const aVal = (a as any)[sortKey];
        const bVal = (b as any)[sortKey];
        
        // Handle null/undefined values
        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;
        
        if (typeof aVal === 'string' && typeof bVal === 'string') {
          comparison = aVal.localeCompare(bVal);
        } else {
          comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
        }
      }
      
      return sortDir === 'asc' ? comparison : -comparison;
    });
  }, [data, sortKey, sortDir, columns]);

  return (
    <div className="w-full">
      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-500 uppercase bg-gray-50/80 border-b border-gray-200">
            <tr>
              {columns.map((col) => (
                <th 
                  key={col.key} 
                  className={`px-4 py-3.5 font-semibold ${col.sortable ? 'cursor-pointer hover:bg-gray-100 transition-colors group select-none' : ''}`}
                  onClick={() => col.sortable ? handleSort(col.key) : undefined}
                >
                  <div className="flex items-center gap-1.5">
                    {col.title}
                    {col.sortable && (
                      <span className="inline-flex flex-col text-gray-400 group-hover:text-gray-600">
                        {sortKey === col.key && sortDir === 'asc' ? (
                          <ArrowUp className="w-3.5 h-3.5 text-blue-600" />
                        ) : sortKey === col.key && sortDir === 'desc' ? (
                          <ArrowDown className="w-3.5 h-3.5 text-blue-600" />
                        ) : (
                          <ChevronsUpDown className="w-3.5 h-3.5 opacity-50" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="border-b-0">
                  {emptyState}
                </td>
              </tr>
            ) : (
              sortedData.map((row) => (
                <tr key={keyExtractor(row)} className="border-b border-gray-100 last:border-0 hover:bg-gray-50/50 transition-colors">
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 align-middle text-gray-700">
                      {col.render ? col.render(row) : (row as any)[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {pagination && (
        <Pagination {...pagination} />
      )}
    </div>
  );
}
