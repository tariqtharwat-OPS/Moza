"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="absolute right-2 top-2 rounded-md bg-zinc-800/80 px-2 py-1 text-xs text-zinc-400 opacity-0 transition-opacity hover:bg-zinc-700/80 hover:text-zinc-200 group-hover/code:opacity-100"
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

function CodeBlock({ className, children, ...props }: React.ComponentPropsWithoutRef<"code">) {
  const match = /language-(\w+)/.exec(className || "");
  const isInline = !match && !className;
  const text = String(children).replace(/\n$/, "");

  if (isInline) {
    return (
      <code className="rounded-md bg-zinc-800 px-1.5 py-0.5 font-mono text-sm text-amber-300" {...props}>
        {children}
      </code>
    );
  }

  return (
    <div className="group/code relative my-2 overflow-hidden rounded-xl border border-zinc-700/50 bg-zinc-900/80">
      {match && (
        <div className="border-b border-zinc-800 px-3 py-1.5 text-xs font-medium uppercase tracking-wider text-zinc-500">
          {match[1]}
        </div>
      )}
      <CopyButton text={text} />
      <pre className="overflow-x-auto p-3 font-mono text-sm leading-relaxed text-zinc-200">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    </div>
  );
}

interface Props {
  role: "user" | "agent";
  content: string;
  timestamp?: string;
  onTimestampClick?: () => void;
}

export default function MessageBubble({ role, content, timestamp, onTimestampClick }: Props) {
  if (!content) return null;

  if (role === "user") {
    return (
      <div className="flex animate-slide-up justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-md bg-indigo-600/20 px-4 py-2.5 text-sm leading-relaxed text-zinc-100 ring-1 ring-indigo-500/20">
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="group animate-slide-up">
      <div className="prose prose-invert max-w-none rounded-2xl rounded-bl-md bg-zinc-800/50 px-4 py-2.5 text-sm leading-relaxed text-zinc-200 ring-1 ring-zinc-700/30">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ className, children, ...props }) {
              return (
                <CodeBlock className={className} {...props}>
                  {children}
                </CodeBlock>
              );
            },
            a({ href, children }) {
              return (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-400 underline underline-offset-2 hover:text-blue-300">
                  {children}
                </a>
              );
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
      {timestamp && (
        <div
          onClick={onTimestampClick}
          className="mt-1 cursor-default px-1 text-[10px] text-zinc-600 opacity-0 transition-opacity group-hover:opacity-100"
        >
          {timestamp}
        </div>
      )}
    </div>
  );
}
