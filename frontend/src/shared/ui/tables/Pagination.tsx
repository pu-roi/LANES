import React from "react";
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import { Button } from "../forms/Button";

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  disabled?: boolean;
}

export function Pagination({ page, totalPages, onPageChange, disabled = false }: PaginationProps) {
  if (totalPages <= 1) return null;

  // Simple rendering of pages, can show a window if totalPages is large
  const getPageNumbers = () => {
    const pages = [];
    let start = Math.max(1, page - 2);
    let end = Math.min(totalPages, page + 2);

    if (end - start < 4) {
      if (start === 1) end = Math.min(totalPages, 5);
      else if (end === totalPages) start = Math.max(1, totalPages - 4);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };

  const pages = getPageNumbers();

  return (
    <div className="flex items-center justify-between bg-white px-4 py-3 rounded-xl border border-gray-200 shadow-sm mt-4">
      <div className="flex flex-1 justify-between sm:hidden">
        <Button
          onClick={() => onPageChange(Math.max(page - 1, 1))}
          disabled={page === 1 || disabled}
          variant="outline"
          className="text-xs"
        >
          Previous
        </Button>
        <Button
          onClick={() => onPageChange(Math.min(page + 1, totalPages))}
          disabled={page === totalPages || disabled}
          variant="outline"
          className="text-xs"
        >
          Next
        </Button>
      </div>
      <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
        <div>
          <p className="text-xs md:text-sm text-gray-600">
            Showing Page <span className="font-semibold text-gray-900">{page}</span> of{" "}
            <span className="font-semibold text-gray-900">{totalPages}</span>
          </p>
        </div>
        <div className="flex items-center gap-1">
          <Button
            onClick={() => onPageChange(1)}
            disabled={page === 1 || disabled}
            variant="ghost"
            className="p-1 hidden sm:flex text-gray-500 hover:text-gray-700"
            title="First Page"
          >
            <ChevronsLeft className="w-4 h-4" />
          </Button>
          <Button
            onClick={() => onPageChange(Math.max(page - 1, 1))}
            disabled={page === 1 || disabled}
            variant="ghost"
            className="p-1 text-gray-500 hover:text-gray-700"
            title="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>

          {pages[0] > 1 && (
            <>
              <Button variant="ghost" className="px-3 py-1 text-sm font-medium text-gray-500" onClick={() => onPageChange(1)}>1</Button>
              {pages[0] > 2 && <span className="px-2 text-gray-400">...</span>}
            </>
          )}

          {pages.map((p) => (
            <Button
              key={p}
              onClick={() => onPageChange(p)}
              disabled={disabled}
              variant={page === p ? "primary" : "ghost"}
              className={`px-3 py-1 text-sm font-medium ${
                page === p
                  ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {p}
            </Button>
          ))}

          {pages[pages.length - 1] < totalPages && (
            <>
              {pages[pages.length - 1] < totalPages - 1 && <span className="px-2 text-gray-400">...</span>}
              <Button variant="ghost" className="px-3 py-1 text-sm font-medium text-gray-500" onClick={() => onPageChange(totalPages)}>{totalPages}</Button>
            </>
          )}

          <Button
            onClick={() => onPageChange(Math.min(page + 1, totalPages))}
            disabled={page === totalPages || disabled}
            variant="ghost"
            className="p-1 text-gray-500 hover:text-gray-700"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
          <Button
            onClick={() => onPageChange(totalPages)}
            disabled={page === totalPages || disabled}
            variant="ghost"
            className="p-1 hidden sm:flex text-gray-500 hover:text-gray-700"
            title="Last Page"
          >
            <ChevronsRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
