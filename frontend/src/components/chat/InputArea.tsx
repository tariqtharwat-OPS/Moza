"use client";

import { useRef, useCallback, type KeyboardEvent, type FormEvent } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: FormEvent) => void;
  onStop?: () => void;
  isProcessing?: boolean;
  placeholder?: string;
}

export default function InputArea({ value, onChange, onSubmit, onStop, isProcessing, placeholder }: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (value.trim()) {
          onSubmit(e as unknown as FormEvent);
        }
      }
    },
    [value, onSubmit]
  );

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }
  }, []);

  return (
    <form onSubmit={onSubmit} className="border-t border-zinc-800 bg-zinc-950/80 px-4 py-3 backdrop-blur-sm">
      <div className="mx-auto flex max-w-3xl items-end gap-3">
        <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              adjustHeight();
            }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || "Ask MOZA to perform a task..."}
            rows={3}
            className="w-full resize-none rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 pr-12 text-sm leading-relaxed text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20"
          />
        </div>
        {isProcessing ? (
          <button
            type="button"
            onClick={onStop}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-red-600 text-white transition-all hover:bg-red-500"
            title="Stop task"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="1.5" />
            </svg>
          </button>
        ) : (
          <button
            type="submit"
            disabled={!value.trim()}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white transition-all hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        )}
      </div>
    </form>
  );
}
